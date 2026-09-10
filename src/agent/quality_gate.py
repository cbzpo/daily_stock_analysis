"""
Data Quality Gate — validates data integrity before each pipeline stage.

Checks price validity, freshness, completeness, and consistency.
Attaches warnings to AgentContext.meta["data_warnings"] for downstream consumption.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityWarning:
    category: str  # price, freshness, completeness, consistency
    severity: str  # critical, warning, info
    message: str
    field_name: str = ""


@dataclass
class QualityReport:
    passed: bool = True
    warnings: List[QualityWarning] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0

    def add(self, w: QualityWarning) -> None:
        self.warnings.append(w)
        if w.severity == "critical":
            self.critical_count += 1
            self.passed = False
        elif w.severity == "warning":
            self.warning_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "warnings": [
                {"category": w.category, "severity": w.severity, "message": w.message}
                for w in self.warnings
            ],
        }


class DataQualityGate:
    """Validates data quality before each pipeline stage."""

    def __init__(
        self,
        enabled: bool = True,
        staleness_threshold_s: float = 300.0,
        max_pct_change: float = 20.0,
    ):
        self.enabled = enabled
        self.staleness_threshold_s = staleness_threshold_s
        self.max_pct_change = max_pct_change

    def validate(
        self,
        ctx: Any,
        stage_name: str = "",
        check_quote: bool = True,
        check_history: bool = True,
        check_chip: bool = False,
    ) -> QualityReport:
        """Run quality checks and attach warnings to ctx.meta."""
        if not self.enabled:
            return QualityReport(passed=True)

        report = QualityReport()

        if check_quote:
            self._validate_quote(ctx, report)

        if check_history:
            self._validate_history(ctx, report)

        if check_chip:
            self._validate_chip(ctx, report)

        # Attach to context
        existing = ctx.meta.get("data_warnings", [])
        existing.extend(report.to_dict())
        ctx.meta["data_warnings"] = existing

        if report.warnings:
            logger.warning(
                "[QualityGate] %s: %d warnings (%d critical)",
                stage_name or "unknown",
                len(report.warnings),
                report.critical_count,
            )

        return report

    def _validate_quote(self, ctx: Any, report: QualityReport) -> None:
        quote = ctx.get_data("realtime_quote")
        if not quote:
            report.add(QualityWarning(
                category="completeness",
                severity="warning",
                message="No realtime quote data available",
                field_name="realtime_quote",
            ))
            return

        # Price validity
        last_price = quote.get("last_price") or quote.get("close")
        if last_price is None or (isinstance(last_price, float) and math.isnan(last_price)):
            report.add(QualityWarning(
                category="price",
                severity="critical",
                message="Realtime quote has no valid last_price",
                field_name="last_price",
            ))
        elif last_price <= 0:
            report.add(QualityWarning(
                category="price",
                severity="critical",
                message=f"Realtime last_price is non-positive: {last_price}",
                field_name="last_price",
            ))

        # High/low consistency
        high = quote.get("high")
        low = quote.get("low")
        if high is not None and low is not None:
            if isinstance(high, (int, float)) and isinstance(low, (int, float)):
                if not math.isnan(high) and not math.isnan(low):
                    if high < low:
                        report.add(QualityWarning(
                            category="consistency",
                            severity="warning",
                            message=f"high ({high}) < low ({low})",
                            field_name="high/low",
                        ))

        # Freshness
        fetched_at = quote.get("fetched_at")
        stale_seconds = quote.get("stale_seconds")
        if stale_seconds is not None and isinstance(stale_seconds, (int, float)):
            if stale_seconds > self.staleness_threshold_s:
                report.add(QualityWarning(
                    category="freshness",
                    severity="warning",
                    message=f"Quote is {stale_seconds:.0f}s old (threshold: {self.staleness_threshold_s:.0f}s)",
                    field_name="stale_seconds",
                ))

    def _validate_history(self, ctx: Any, report: QualityReport) -> None:
        history = ctx.get_data("daily_history")
        if not history:
            # History is optional for some stages
            return

        if isinstance(history, list) and len(history) > 0:
            latest = history[-1]
            for field_name in ("close", "open", "high", "low"):
                val = latest.get(field_name)
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    report.add(QualityWarning(
                        category="price",
                        severity="warning",
                        message=f"Latest daily bar missing {field_name}",
                        field_name=field_name,
                    ))

            # pct_chg bounds (A-share ±20%)
            pct_chg = latest.get("pct_chg")
            if pct_chg is not None and isinstance(pct_chg, (int, float)):
                if not math.isnan(pct_chg) and abs(pct_chg) > self.max_pct_change:
                    report.add(QualityWarning(
                        category="consistency",
                        severity="warning",
                        message=f"pct_chg={pct_chg:.2f}% exceeds ±{self.max_pct_change}% bound",
                        field_name="pct_chg",
                    ))

    def _validate_chip(self, ctx: Any, report: QualityReport) -> None:
        chip = ctx.get_data("chip_distribution")
        if not chip:
            return

        avg_cost = chip.get("avg_cost")
        concentration = chip.get("concentration_90")

        if avg_cost is not None and isinstance(avg_cost, (int, float)):
            if avg_cost <= 0:
                report.add(QualityWarning(
                    category="consistency",
                    severity="warning",
                    message=f"Chip avg_cost is non-positive: {avg_cost}",
                    field_name="avg_cost",
                ))

        if concentration is not None and isinstance(concentration, (int, float)):
            if concentration < 0:
                report.add(QualityWarning(
                    category="consistency",
                    severity="warning",
                    message=f"Chip concentration is negative: {concentration}",
                    field_name="concentration_90",
                ))
