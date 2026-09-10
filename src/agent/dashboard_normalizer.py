# -*- coding: utf-8 -*-
"""
Dashboard normalizer — shapes raw LLM output into the dashboard schema.

Extracted from ``orchestrator.py`` to reduce its size and make the
normalization logic independently testable.  All functions in this module
are pure (no side effects) except :func:`normalize_dashboard_payload`
which mutates the *payload* dict in place and returns it.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.agent.protocols import AgentContext, AgentOpinion, normalize_decision_signal


# ============================================================
# Pure helper functions
# ============================================================

def coerce_level_value(value: Any) -> Any:
    """Normalize a price-level value to float or string, or None if invalid."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    text = str(value).replace(",", "").replace("，", "").strip()
    if not text or text.upper() == "N/A" or text in {"-", "—"}:
        return None
    try:
        return round(float(text), 2)
    except ValueError:
        return text


def pick_first_level(*values: Any) -> Any:
    """Return the first non-None level from a list of candidates."""
    for value in values:
        normalized = coerce_level_value(value)
        if normalized is not None:
            return normalized
    return None


def level_values_equal(left: Any, right: Any) -> bool:
    """Check if two level values are equal after normalization."""
    left_normalized = coerce_level_value(left)
    right_normalized = coerce_level_value(right)
    return (
        left_normalized is not None
        and right_normalized is not None
        and left_normalized == right_normalized
    )


def first_non_empty_text(*values: Any) -> str:
    """Return the first non-empty string from *values*."""
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def truncate_text(text: Any, limit: int) -> str:
    """Truncate *text* to *limit* characters, appending '…' if needed."""
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def extract_latest_news_title(intelligence: Dict[str, Any]) -> str:
    """Pull the first news title from the intelligence block."""
    key_news = intelligence.get("key_news")
    if isinstance(key_news, list):
        for item in key_news:
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                if title:
                    return title
    latest_news = intelligence.get("latest_news")
    if isinstance(latest_news, str) and latest_news.strip():
        return latest_news.strip()
    return ""


def signal_to_operation(signal: str) -> str:
    """Map a decision signal to a Chinese operation label."""
    mapping = {
        "buy": "买入",
        "hold": "观望",
        "sell": "减仓/卖出",
    }
    return mapping.get(signal, "观望")


def signal_to_signal_type(signal: str) -> str:
    """Map a decision signal to a display label with emoji."""
    mapping = {
        "buy": "🟢买入信号",
        "hold": "⚪观望信号",
        "sell": "🔴卖出信号",
    }
    return mapping.get(signal, "⚪观望信号")


def default_position_advice(signal: str) -> Dict[str, str]:
    """Return default no_position / has_position text for *signal*."""
    mapping = {
        "buy": {
            "no_position": "可结合支撑位分批试仓，避免一次性追高。",
            "has_position": "可继续持有，回踩关键位不破再考虑加仓。",
        },
        "hold": {
            "no_position": "暂不追高，等待更清晰的入场条件。",
            "has_position": "以观察为主，跌破止损位再执行风控。",
        },
        "sell": {
            "no_position": "暂不参与，等待风险充分释放。",
            "has_position": "优先控制回撤，按计划减仓或离场。",
        },
    }
    return mapping.get(signal, mapping["hold"])


def default_position_size(signal: str) -> str:
    """Return a default position-size label for *signal*."""
    mapping = {
        "buy": "轻仓试仓",
        "hold": "控制仓位",
        "sell": "降仓防守",
    }
    return mapping.get(signal, "控制仓位")


def normalize_operation_advice_value(value: Any, signal: str) -> str:
    """Coerce *value* to a string; fall back to signal-based default."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return signal_to_operation(signal)


def confidence_label(confidence: float) -> str:
    """Map a 0-1 confidence to a Chinese label (高/中/低)."""
    if confidence >= 0.75:
        return "高"
    if confidence >= 0.45:
        return "中"
    return "低"


def estimate_sentiment_score(signal: str, confidence: float) -> int:
    """Estimate a sentiment score (0-100) from *signal* and *confidence*."""
    confidence = max(0.0, min(1.0, float(confidence)))
    bands = {
        "buy": (65, 79),
        "hold": (45, 59),
        "sell": (20, 39),
    }
    low, high = bands.get(signal, (45, 59))
    return int(round(low + (high - low) * confidence))


def adjust_sentiment_score(score: int, signal: str) -> int:
    """Clamp sentiment score into the target band for the overridden signal."""
    bands = {
        "buy": (60, 79),
        "hold": (40, 59),
        "sell": (0, 39),
    }
    low, high = bands.get(signal, (0, 100))
    return max(low, min(high, score))


def adjust_operation_advice(advice: str, signal: str) -> str:
    """Normalize action wording to the overridden decision signal."""
    mapping = {
        "buy": "买入",
        "hold": "观望",
        "sell": "减仓/卖出",
    }
    if signal not in mapping:
        return advice
    if advice == mapping[signal]:
        return advice
    return f"{mapping[signal]}（原建议已被风控下调）"


# ============================================================
# Context-dependent helpers (used by normalize_dashboard_payload)
# ============================================================

def _latest_opinion(ctx: AgentContext, names: set[str]) -> Optional[AgentOpinion]:
    """Return the most recent opinion whose agent_name is in *names*."""
    for opinion in reversed(ctx.opinions):
        if opinion.agent_name in names:
            return opinion
    return None


def _select_base_opinion(ctx: AgentContext) -> Optional[AgentOpinion]:
    """Pick the most authoritative opinion from the context."""
    preferred_groups = (
        {"decision"},
        {"skill_consensus", "strategy_consensus"},
        {"technical"},
        {"intel"},
        {"risk"},
    )
    for names in preferred_groups:
        opinion = _latest_opinion(ctx, names)
        if opinion is not None:
            return opinion
    if ctx.opinions:
        return ctx.opinions[-1]
    return None


def _collect_key_levels(
    ctx: AgentContext,
    payload: Dict[str, Any],
    dashboard_block: Dict[str, Any],
) -> Dict[str, Any]:
    """Collect key price levels from dashboard payloads and agent opinions."""
    levels: Dict[str, Any] = {}

    def absorb(source: Any) -> None:
        if not isinstance(source, dict):
            return
        for key, value in source.items():
            normalized = coerce_level_value(value)
            if normalized is not None and key not in levels:
                levels[key] = normalized

    absorb(payload.get("key_levels"))
    absorb(dashboard_block.get("key_levels"))
    for opinion in reversed(ctx.opinions):
        absorb(getattr(opinion, "key_levels", {}))
        raw = opinion.raw_data if isinstance(opinion.raw_data, dict) else {}
        absorb(raw.get("key_levels"))
    return levels


def _build_data_perspective(
    ctx: AgentContext,
    key_levels: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a lightweight data_perspective block from cached market data."""
    realtime = ctx.get_data("realtime_quote")
    chip = ctx.get_data("chip_distribution")
    trend = ctx.get_data("trend_result")
    technical = _latest_opinion(ctx, {"technical"})
    tech_raw = technical.raw_data if technical and isinstance(technical.raw_data, dict) else {}
    trend_dict = trend if isinstance(trend, dict) else {}

    data_perspective: Dict[str, Any] = {}
    ma_alignment = tech_raw.get("ma_alignment")
    trend_score = tech_raw.get("trend_score")
    if ma_alignment or trend_score is not None:
        data_perspective["trend_status"] = {
            "ma_alignment": ma_alignment or "N/A",
            "trend_score": trend_score if trend_score is not None else "N/A",
            "is_bullish": str(ma_alignment).lower() == "bullish",
        }

    def _bias_label(bias):
        if not isinstance(bias, (int, float)):
            return ""
        if bias > 5:
            return "超买"
        elif bias > 2:
            return "偏高"
        elif bias < -5:
            return "超卖"
        elif bias < -2:
            return "偏低"
        return "中性"

    def _r(val, n=2):
        return round(val, n) if isinstance(val, (int, float)) else val

    def _pick(primary_dict, primary_key, fallback_dict, fallback_key, default="N/A"):
        v = primary_dict.get(primary_key)
        if v is not None:
            return v
        v2 = fallback_dict.get(fallback_key, default)
        return v2 if v2 is not None else default

    if isinstance(realtime, dict) or trend_dict:
        data_perspective["price_position"] = {
            "current_price": _r(_pick(trend_dict, "current_price", realtime or {}, "price")),
            "ma5": _r(_pick(trend_dict, "ma5", tech_raw, "ma5")),
            "ma10": _r(_pick(trend_dict, "ma10", tech_raw, "ma10")),
            "ma20": _r(_pick(trend_dict, "ma20", tech_raw, "ma20")),
            "bias_ma5": _r(_pick(trend_dict, "bias_ma5", tech_raw, "bias_ma5")),
            "bias_status": _bias_label(trend_dict.get("bias_ma5")) or tech_raw.get("bias_status", "N/A"),
            "support_level": key_levels.get("support") or key_levels.get("immediate_support") or "N/A",
            "resistance_level": key_levels.get("resistance") or key_levels.get("current_resistance") or "N/A",
        }
        data_perspective["volume_analysis"] = {
            "volume_ratio": (realtime or {}).get("volume_ratio", "N/A"),
            "turnover_rate": (realtime or {}).get("turnover_rate", "N/A"),
            "volume_status": trend_dict.get("volume_status") or tech_raw.get("volume_status", "N/A"),
            "volume_meaning": tech_raw.get("reasoning", "") if tech_raw else "",
        }

    if isinstance(chip, dict):
        concentration = chip.get("concentration_90")
        if concentration is None:
            concentration = chip.get("concentration")
        data_perspective["chip_structure"] = {
            "profit_ratio": chip.get("profit_ratio", "N/A"),
            "avg_cost": chip.get("avg_cost", "N/A"),
            "concentration": concentration if concentration is not None else "N/A",
            "chip_health": chip.get("chip_health", "一般"),
        }

    return data_perspective


def _collect_risk_alerts(
    ctx: AgentContext,
    intelligence: Dict[str, Any],
) -> List[str]:
    """Gather risk alerts from intelligence block and agent opinions."""
    alerts: List[str] = []

    def absorb(values: Any) -> None:
        if not isinstance(values, list):
            return
        for item in values:
            text = ""
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = str(item.get("description") or item.get("title") or "").strip()
            if text and text not in alerts:
                alerts.append(text)

    absorb(intelligence.get("risk_alerts"))
    intel = _latest_opinion(ctx, {"intel"})
    intel_raw = intel.raw_data if intel and isinstance(intel.raw_data, dict) else {}
    absorb(intel_raw.get("risk_alerts"))
    risk = _latest_opinion(ctx, {"risk"})
    risk_raw = risk.raw_data if risk and isinstance(risk.raw_data, dict) else {}
    absorb(risk_raw.get("flags"))
    for flag in ctx.risk_flags:
        description = str(flag.get("description", "")).strip()
        if description and description not in alerts:
            alerts.append(description)
    return alerts[:8]


def _collect_positive_catalysts(
    ctx: AgentContext,
    intelligence: Dict[str, Any],
) -> List[str]:
    """Gather positive catalysts from intelligence block and agent opinions."""
    catalysts: List[str] = []

    def absorb(values: Any) -> None:
        if not isinstance(values, list):
            return
        for item in values:
            text = str(item).strip()
            if text and text not in catalysts:
                catalysts.append(text)

    absorb(intelligence.get("positive_catalysts"))
    intel = _latest_opinion(ctx, {"intel"})
    intel_raw = intel.raw_data if intel and isinstance(intel.raw_data, dict) else {}
    absorb(intel_raw.get("positive_catalysts"))
    return catalysts[:8]


# ============================================================
# Main normalization entry point
# ============================================================

def normalize_dashboard_payload(
    payload: Optional[Dict[str, Any]],
    ctx: AgentContext,
) -> Optional[Dict[str, Any]]:
    """Normalize or synthesize the dashboard shape expected downstream.

    This is the single entry point extracted from
    ``AgentOrchestrator._normalize_dashboard_payload``.
    """
    payload = dict(payload or {})
    meaningful_data_keys = (
        "realtime_quote",
        "daily_history",
        "chip_distribution",
        "trend_result",
        "news_context",
        "intel_opinion",
        "fundamental_context",
    )
    has_meaningful_context = any(ctx.get_data(key) is not None for key in meaningful_data_keys)
    if not payload and not ctx.opinions and not has_meaningful_context:
        return None

    base_opinion = _select_base_opinion(ctx)
    decision_type = normalize_decision_signal(
        payload.get("decision_type") or (base_opinion.signal if base_opinion else "hold")
    )
    confidence = float(base_opinion.confidence if base_opinion is not None else 0.5)
    sentiment_score = payload.get("sentiment_score")
    try:
        sentiment_score = int(sentiment_score)
    except (TypeError, ValueError):
        sentiment_score = estimate_sentiment_score(decision_type, confidence)

    dashboard_block = payload.get("dashboard")
    if not isinstance(dashboard_block, dict):
        dashboard_block = {}
    else:
        dashboard_block = dict(dashboard_block)

    core = dashboard_block.get("core_conclusion")
    if not isinstance(core, dict):
        core = {}
    else:
        core = dict(core)

    intelligence = dashboard_block.get("intelligence")
    if not isinstance(intelligence, dict):
        intelligence = {}
    else:
        intelligence = dict(intelligence)

    battle = dashboard_block.get("battle_plan")
    if not isinstance(battle, dict):
        battle = {}
    else:
        battle = dict(battle)

    analysis_summary = first_non_empty_text(
        payload.get("analysis_summary"),
        core.get("one_sentence"),
        getattr(base_opinion, "reasoning", ""),
    )
    if not analysis_summary:
        analysis_summary = f"多 Agent 未生成完整仪表盘，当前按{signal_to_operation(decision_type)}处理。"
    analysis_summary = truncate_text(analysis_summary, 220)

    trend_prediction = first_non_empty_text(
        payload.get("trend_prediction"),
        (getattr(base_opinion, "raw_data", {}) or {}).get("trend_summary")
        if base_opinion is not None else "",
    )
    if not trend_prediction:
        technical = _latest_opinion(ctx, {"technical"})
        tech_raw = technical.raw_data if technical and isinstance(technical.raw_data, dict) else {}
        ma_alignment = tech_raw.get("ma_alignment")
        trend_score = tech_raw.get("trend_score")
        if ma_alignment or trend_score is not None:
            trend_prediction = f"技术面{ma_alignment or 'neutral'}，趋势评分 {trend_score if trend_score is not None else 'N/A'}"
        else:
            trend_prediction = "待结合更多阶段结果确认"

    operation_advice_raw = payload.get("operation_advice")
    operation_advice = normalize_operation_advice_value(operation_advice_raw, decision_type)

    existing_position = core.get("position_advice")
    position_advice = dict(existing_position) if isinstance(existing_position, dict) else {}
    if isinstance(operation_advice_raw, dict):
        no_position = first_non_empty_text(
            operation_advice_raw.get("no_position"),
            operation_advice_raw.get("empty_position"),
        )
        has_position = first_non_empty_text(
            operation_advice_raw.get("has_position"),
            operation_advice_raw.get("holding_position"),
        )
        if no_position and "no_position" not in position_advice:
            position_advice["no_position"] = no_position
        if has_position and "has_position" not in position_advice:
            position_advice["has_position"] = has_position
    defaults = default_position_advice(decision_type)
    position_advice.setdefault("no_position", defaults["no_position"])
    position_advice.setdefault("has_position", defaults["has_position"])

    key_levels = _collect_key_levels(ctx, payload, dashboard_block)
    sniper = battle.get("sniper_points")
    if not isinstance(sniper, dict):
        sniper = {}
    else:
        sniper = dict(sniper)

    ideal_buy = pick_first_level(
        sniper.get("ideal_buy"),
        key_levels.get("ideal_buy_if_valuation_improves"),
        key_levels.get("ideal_buy"),
        key_levels.get("support"),
        key_levels.get("immediate_support"),
    )
    sniper["ideal_buy"] = ideal_buy if ideal_buy is not None else "N/A"

    secondary_buy = coerce_level_value(sniper.get("secondary_buy"))
    if secondary_buy is None:
        secondary_buy = pick_first_level(
            key_levels.get("secondary_buy"),
            key_levels.get("support"),
            key_levels.get("immediate_support"),
        )
    if level_values_equal(secondary_buy, sniper.get("ideal_buy")):
        secondary_buy = None
    sniper["secondary_buy"] = secondary_buy if secondary_buy is not None else "N/A"
    sniper.setdefault(
        "stop_loss",
        key_levels.get("stop_loss")
        or key_levels.get("strong_support_stop_loss")
        or "待补充",
    )
    sniper.setdefault(
        "take_profit",
        key_levels.get("take_profit")
        or key_levels.get("next_breakout_target")
        or key_levels.get("current_resistance")
        or key_levels.get("resistance")
        or "N/A",
    )

    risk_alerts = _collect_risk_alerts(ctx, intelligence)
    positive_catalysts = _collect_positive_catalysts(ctx, intelligence)
    latest_news = extract_latest_news_title(intelligence)

    if not intelligence.get("risk_alerts"):
        intelligence["risk_alerts"] = risk_alerts
    if positive_catalysts and not intelligence.get("positive_catalysts"):
        intelligence["positive_catalysts"] = positive_catalysts
    if latest_news and not intelligence.get("latest_news"):
        intelligence["latest_news"] = latest_news

    if not core.get("one_sentence"):
        core["one_sentence"] = truncate_text(analysis_summary, 60)
    if not core.get("time_sensitivity"):
        core["time_sensitivity"] = "本周内"
    if not core.get("signal_type"):
        core["signal_type"] = signal_to_signal_type(decision_type)
    core["position_advice"] = position_advice

    battle["sniper_points"] = sniper
    if "action_checklist" not in battle:
        battle["action_checklist"] = []
    position_strategy = battle.get("position_strategy")
    if not isinstance(position_strategy, dict) or not position_strategy:
        battle["position_strategy"] = {
            "suggested_position": default_position_size(decision_type),
            "entry_plan": position_advice["no_position"],
            "risk_control": f"止损参考 {sniper.get('stop_loss', '待补充')}",
        }

    data_perspective = dashboard_block.get("data_perspective")
    if not isinstance(data_perspective, dict):
        data_perspective = {}
    if not data_perspective:
        built_data_perspective = _build_data_perspective(ctx, key_levels)
        if built_data_perspective:
            data_perspective = built_data_perspective
    if data_perspective:
        dashboard_block["data_perspective"] = data_perspective

    dashboard_block["core_conclusion"] = core
    dashboard_block["intelligence"] = intelligence
    dashboard_block["battle_plan"] = battle

    key_points = payload.get("key_points")
    if not isinstance(key_points, list) or not key_points:
        key_points = [
            truncate_text(op.reasoning, 120)
            for op in ctx.opinions
            if isinstance(op.reasoning, str) and op.reasoning.strip()
        ][:5]

    risk_warning = first_non_empty_text(
        payload.get("risk_warning"),
        "；".join(risk_alerts[:3]),
        getattr(_latest_opinion(ctx, {"risk"}), "reasoning", ""),
    )
    if not risk_warning:
        risk_warning = "暂无额外风险提示"

    payload["stock_name"] = first_non_empty_text(payload.get("stock_name"), ctx.stock_name, ctx.stock_code)
    payload["sentiment_score"] = sentiment_score
    payload["trend_prediction"] = trend_prediction
    payload["operation_advice"] = operation_advice
    payload["decision_type"] = decision_type
    payload["confidence_level"] = confidence_label(confidence)
    payload["analysis_summary"] = analysis_summary
    payload["key_points"] = key_points
    payload["risk_warning"] = risk_warning
    payload["dashboard"] = dashboard_block
    return payload
