# -*- coding: utf-8 -*-
"""
IntelAgent — news & intelligence gathering specialist.

Responsible for:
- Searching latest stock news and announcements
- Running comprehensive intelligence search
- Detecting risk events (reduce holdings, earnings warnings, regulatory)
- Summarising sentiment and catalysts
- Quantifying weighted sentiment by news category and recency
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional

from src.agent.agents.base_agent import BaseAgent
from src.agent.protocols import AgentContext, AgentOpinion
from src.agent.runner import try_parse_json

logger = logging.getLogger(__name__)

# Sentiment weight matrix by news category
SENTIMENT_WEIGHTS = {
    "earnings": 1.0,       # 业绩超预期、营收增长
    "policy": 0.9,         # 降准降息、行业政策
    "insider": 0.85,       # 增持减持、股权变动
    "industry": 0.7,       # 行业景气度、技术突破
    "company": 0.5,        # 新品发布、合作签约
    "chatter": 0.2,        # 分析师点评、社交媒体
}

# Category detection keywords
CATEGORY_KEYWORDS = {
    "earnings": ["业绩", "营收", "利润", "财报", "盈利", "亏损", "净利", "毛利", "增长", "下滑", "超预期", "预增", "预减", "预亏", "预盈"],
    "policy": ["政策", "降准", "降息", "加息", "监管", "法规", "条例", "改革", "补贴", "税收", "利率", "货币政策"],
    "insider": ["增持", "减持", "回购", "股权", "董事", "高管", "大股东", "解禁", "质押", "转让"],
    "industry": ["行业", "景气", "产能", "供需", "技术", "突破", "创新", "研发", "专利", "订单"],
    "company": ["发布", "合作", "签约", "中标", "并购", "重组", "扩产", "投产", "上市"],
}

# Recency decay constant (half-life ~14 hours)
RECENCY_LAMBDA = 0.05


def classify_news_category(title: str, snippet: str = "") -> str:
    """Classify news into a sentiment weight category."""
    text = f"{title} {snippet}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "chatter"


def calculate_recency_decay(publish_time: Optional[float]) -> float:
    """Calculate recency decay factor. Returns 1.0 for missing/unknown time."""
    if publish_time is None:
        return 0.5  # neutral for unknown age
    hours_ago = (time.time() - publish_time) / 3600.0
    return math.exp(-RECENCY_LAMBDA * hours_ago)


def aggregate_weighted_sentiment(news_items: List[Dict[str, Any]]) -> float:
    """Calculate weighted sentiment score (0-100) from news items.

    Each item should have:
    - sentiment: float (-1.0 to 1.0) or None
    - publish_time: float (unix timestamp) or None
    - title: str
    - snippet: str (optional)
    """
    total_weight = 0.0
    total_score = 0.0

    for item in news_items:
        sentiment = item.get("sentiment")
        if sentiment is None:
            continue
        try:
            sentiment = float(sentiment)
        except (TypeError, ValueError):
            continue

        # Clamp to [-1, 1]
        sentiment = max(-1.0, min(1.0, sentiment))

        category = classify_news_category(
            item.get("title", ""),
            item.get("snippet", ""),
        )
        weight = SENTIMENT_WEIGHTS.get(category, 0.2)
        recency = calculate_recency_decay(item.get("publish_time"))

        total_weight += weight * recency
        total_score += weight * recency * sentiment

    if total_weight == 0:
        return 50.0  # neutral default

    # Normalize to 0-100 scale (sentiment is -1 to 1, map to 0-100)
    normalized = (total_score / total_weight + 1.0) * 50.0
    return max(0.0, min(100.0, normalized))


class IntelAgent(BaseAgent):
    agent_name = "intel"
    max_steps = 4
    tool_names = [
        "search_stock_news",
        "search_comprehensive_intel",
        "get_stock_info",
        "get_capital_flow",
    ]

    def system_prompt(self, ctx: AgentContext) -> str:
        return """\
You are an **Intelligence & Sentiment Agent** specialising in A-shares, \
HK, and US equities.

Your task: gather the latest news, announcements, and risk signals for \
the given stock, then produce a structured JSON opinion.

## Workflow
1. Search latest stock news (earnings, announcements, insider activity)
2. Run comprehensive intel search — this covers latest news, company \
announcements (公司公告), market analysis, risk checks, and earnings outlook
3. For A-share stocks, call get_capital_flow to obtain main-force (主力) \
capital inflow/outflow data and include it in your analysis
4. Classify positive catalysts and risk alerts
5. Assess overall sentiment

## Risk Detection Priorities
- Insider / major shareholder sell-downs (减持)
- Earnings warnings or pre-loss announcements (业绩预亏)
- Regulatory penalties or investigations
- Industry-wide policy headwinds
- Large lock-up expirations (解禁)
- PE valuation anomalies
- Sustained main-force capital outflow (主力持续净流出)

## Capital Flow Interpretation (A-shares only)
- main_net_inflow > 0: bullish signal (主力净流入)
- main_net_inflow < 0: bearish signal (主力净流出)
- inflow_5d / inflow_10d: medium-term accumulation or distribution trend

## Output Format
Return **only** a JSON object:
{
  "signal": "strong_buy|buy|hold|sell|strong_sell",
  "confidence": 0.0-1.0,
  "reasoning": "2-3 sentence summary of news/sentiment/capital-flow findings",
  "risk_alerts": ["list", "of", "detected", "risks"],
  "positive_catalysts": ["list", "of", "catalysts"],
  "sentiment_label": "very_positive|positive|neutral|negative|very_negative",
  "capital_flow_signal": "inflow|outflow|neutral|not_available",
  "key_news": [
    {"title": "...", "impact": "positive|negative|neutral"}
  ]
}
"""

    def build_user_message(self, ctx: AgentContext) -> str:
        parts = [f"Gather intelligence and assess sentiment for stock **{ctx.stock_code}**"]
        if ctx.stock_name:
            parts[0] += f" ({ctx.stock_name})"
        parts.append(
            "Steps:\n"
            "1. Call search_comprehensive_intel to get latest news, company announcements "
            "(公司公告), risk events, and earnings outlook.\n"
            "2. Call get_capital_flow to obtain main-force (主力) capital flow data "
            "(A-share only; skip for HK/US).\n"
            "3. Output the JSON opinion including capital_flow_signal."
        )
        return "\n".join(parts)

    def post_process(self, ctx: AgentContext, raw_text: str) -> Optional[AgentOpinion]:
        parsed = try_parse_json(raw_text)
        if parsed is None:
            logger.warning("[IntelAgent] failed to parse opinion JSON")
            return None

        # Cache parsed intel so downstream agents (especially RiskAgent) can
        # reuse it instead of re-searching the same evidence.
        ctx.set_data("intel_opinion", parsed)

        # Propagate risk alerts to context
        for alert in parsed.get("risk_alerts", []):
            if isinstance(alert, str) and alert:
                ctx.add_risk_flag(category="intel", description=alert)

        # Calculate weighted sentiment score from key_news
        key_news = parsed.get("key_news", [])
        if key_news:
            sentiment_score = aggregate_weighted_sentiment(key_news)
            parsed["sentiment_score"] = sentiment_score
            # Map score to label for backward compatibility
            if sentiment_score >= 70:
                parsed["sentiment_label"] = "very_positive"
            elif sentiment_score >= 55:
                parsed["sentiment_label"] = "positive"
            elif sentiment_score >= 45:
                parsed["sentiment_label"] = "neutral"
            elif sentiment_score >= 30:
                parsed["sentiment_label"] = "negative"
            else:
                parsed["sentiment_label"] = "very_negative"

        return AgentOpinion(
            agent_name=self.agent_name,
            signal=parsed.get("signal", "hold"),
            confidence=float(parsed.get("confidence", 0.5)),
            reasoning=parsed.get("reasoning", ""),
            raw_data=parsed,
        )


