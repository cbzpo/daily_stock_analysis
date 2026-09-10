# -*- coding: utf-8 -*-
"""
Tests for DataQualityGate — validates data integrity before pipeline stages.
"""

import math
import time
import unittest
from dataclasses import dataclass
from typing import Any, Dict

from src.agent.quality_gate import DataQualityGate, QualityReport, QualityWarning


@dataclass
class _FakeContext:
    """Minimal AgentContext stand-in for quality gate tests."""

    data: Dict[str, Any] = None
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.meta is None:
            self.meta = {}

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class TestDataQualityGateDisabled(unittest.TestCase):
    def test_disabled_returns_passed(self):
        gate = DataQualityGate(enabled=False)
        ctx = _FakeContext()
        report = gate.validate(ctx)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)


class TestDataQualityGateQuote(unittest.TestCase):
    def test_no_quote_data(self):
        gate = DataQualityGate()
        ctx = _FakeContext()
        report = gate.validate(ctx, check_history=False)
        self.assertTrue(report.passed)  # missing quote is warning, not critical
        self.assertEqual(report.warning_count, 1)
        self.assertIn("realtime_quote", report.warnings[0].field_name)

    def test_valid_quote(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": 100.0, "high": 102.0, "low": 98.0},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)

    def test_null_last_price(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": None, "high": 102.0, "low": 98.0},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)
        self.assertEqual(report.warnings[0].category, "price")

    def test_nan_last_price(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": float("nan")},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)

    def test_negative_last_price(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": -5.0},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)

    def test_zero_last_price(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": 0},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)

    def test_high_less_than_low(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": 100.0, "high": 95.0, "low": 105.0},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertTrue(report.passed)  # warning, not critical
        self.assertEqual(report.warning_count, 1)
        self.assertEqual(report.warnings[0].category, "consistency")

    def test_stale_quote(self):
        gate = DataQualityGate(staleness_threshold_s=300)
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": 100.0, "stale_seconds": 600},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)
        self.assertEqual(report.warnings[0].category, "freshness")

    def test_fresh_quote_no_warning(self):
        gate = DataQualityGate(staleness_threshold_s=300)
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": 100.0, "stale_seconds": 100},
        })
        report = gate.validate(ctx, check_history=False)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)


class TestDataQualityGateHistory(unittest.TestCase):
    def test_no_history_skipped(self):
        gate = DataQualityGate()
        ctx = _FakeContext()
        report = gate.validate(ctx, check_quote=False)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)

    def test_valid_history(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "daily_history": [
                {"close": 99.0, "open": 98.0, "high": 101.0, "low": 97.0, "pct_chg": 1.5},
                {"close": 100.0, "open": 99.0, "high": 102.0, "low": 98.0, "pct_chg": 2.0},
            ],
        })
        report = gate.validate(ctx, check_quote=False)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)

    def test_missing_field_in_latest_bar(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "daily_history": [
                {"close": None, "open": 98.0, "high": 101.0, "low": 97.0},
            ],
        })
        report = gate.validate(ctx, check_quote=False)
        self.assertTrue(report.passed)  # warning, not critical
        self.assertEqual(report.warning_count, 1)
        self.assertIn("close", report.warnings[0].field_name)

    def test_extreme_pct_chg(self):
        gate = DataQualityGate(max_pct_change=20.0)
        ctx = _FakeContext(data={
            "daily_history": [
                {"close": 100.0, "open": 99.0, "high": 101.0, "low": 99.0, "pct_chg": 25.0},
            ],
        })
        report = gate.validate(ctx, check_quote=False)
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)
        self.assertEqual(report.warnings[0].field_name, "pct_chg")

    def test_normal_pct_chg(self):
        gate = DataQualityGate(max_pct_change=20.0)
        ctx = _FakeContext(data={
            "daily_history": [
                {"close": 100.0, "open": 99.0, "high": 101.0, "low": 99.0, "pct_chg": 5.0},
            ],
        })
        report = gate.validate(ctx, check_quote=False)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.warnings), 0)


class TestDataQualityGateChip(unittest.TestCase):
    def test_no_chip_skipped(self):
        gate = DataQualityGate()
        ctx = _FakeContext()
        report = gate.validate(ctx, check_quote=False, check_history=False, check_chip=True)
        self.assertTrue(report.passed)

    def test_negative_concentration(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "chip_distribution": {"concentration_90": -0.1},
        })
        report = gate.validate(ctx, check_quote=False, check_history=False, check_chip=True)
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)

    def test_nonpositive_avg_cost(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "chip_distribution": {"avg_cost": 0, "concentration_90": 0.5},
        })
        report = gate.validate(ctx, check_quote=False, check_history=False, check_chip=True)
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)


class TestQualityReport(unittest.TestCase):
    def test_add_critical_fails(self):
        report = QualityReport()
        report.add(QualityWarning(category="price", severity="critical", message="bad"))
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)

    def test_add_warning_still_passes(self):
        report = QualityReport()
        report.add(QualityWarning(category="freshness", severity="warning", message="old"))
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)

    def test_to_dict(self):
        report = QualityReport()
        report.add(QualityWarning(category="price", severity="critical", message="bad"))
        d = report.to_dict()
        self.assertFalse(d["passed"])
        self.assertEqual(d["critical_count"], 1)
        self.assertEqual(len(d["warnings"]), 1)
        self.assertEqual(d["warnings"][0]["category"], "price")

    def test_attachments_to_context(self):
        gate = DataQualityGate()
        ctx = _FakeContext(data={
            "realtime_quote": {"last_price": None},
        })
        gate.validate(ctx, stage_name="test")
        self.assertIn("data_warnings", ctx.meta)
        self.assertIsInstance(ctx.meta["data_warnings"], list)


if __name__ == "__main__":
    unittest.main()
