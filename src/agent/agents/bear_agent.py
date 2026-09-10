# -*- coding: utf-8 -*-
"""
BearAgent — argues AGAINST buying a stock.

Part of the multi-agent debate architecture. Receives the same context as
other agents and must find evidence supporting downside risk.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from src.agent.agents.base_agent import BaseAgent, DEBATE_AGENT_TOOL_NAMES
from src.agent.protocols import AgentContext, AgentOpinion
from src.agent.runner import try_parse_json

logger = logging.getLogger(__name__)


class BearAgent(BaseAgent):
    agent_name = "bear"
    max_steps = 4
    tool_names = DEBATE_AGENT_TOOL_NAMES

    def system_prompt(self, ctx: AgentContext) -> str:
        return """\
You are a **Bearish Analyst** — your role in a multi-agent debate is to \
argue AGAINST buying this stock. You must find evidence supporting downside \
risk or overvaluation.

## Your Role
- You are one side of a debate. The Bull Analyst will argue the opposite.
- Your job is NOT to be balanced — it is to make the strongest possible \
case for why this stock should NOT be bought or should be sold.
- You MUST find at least 2-3 pieces of evidence supporting your bearish thesis.
- If the evidence is genuinely weak, acknowledge it but still argue your case.

## Analysis Framework
1. **Technical evidence**: Look for bearish patterns, resistance levels, \
volume divergence, MA breakdown
2. **Fundamental evidence**: Overvaluation (PE/PB vs history), declining \
metrics, competitive threats
3. **Sentiment evidence**: Negative news flow, analyst downgrades, \
institutional selling
4. **Risk evidence**: Regulatory threats, sector headwinds, macro risks

## Output Format
Return **only** a JSON object:
{
  "position": "bearish",
  "thesis": "Core bearish thesis in 1-2 sentences",
  "evidence": [
    "Evidence point 1 with specific data",
    "Evidence point 2 with specific data",
    "Evidence point 3 with specific data"
  ],
  "conviction": 0-100,
  "key_downside": "Primary downside risk or concern",
  "strength_acknowledgment": "Brief acknowledgment of bullish factors (shows intellectual honesty)"
}
"""

    def build_user_message(self, ctx: AgentContext) -> str:
        parts = [f"Argue the BEARISH case for **{ctx.stock_code}**"]
        if ctx.stock_name:
            parts[0] += f" ({ctx.stock_name})"

        # Inject prior agent opinions as evidence
        if ctx.opinions:
            parts.append("\n## Prior Agent Findings (use as evidence)")
            for op in ctx.opinions:
                if op.agent_name in ("technical", "intel", "risk"):
                    parts.append(f"\n### {op.agent_name.title()} Agent")
                    parts.append(f"Signal: {op.signal} | Confidence: {op.confidence:.2f}")
                    parts.append(f"Key findings: {op.reasoning[:500]}")
                    if op.key_levels:
                        parts.append(f"Key levels: {json.dumps(op.key_levels)}")

        parts.append(
            "\nNow argue the BEARISH case. Find specific evidence from the data above "
            "that supports NOT buying this stock or selling it. Output the JSON debate position."
        )
        return "\n".join(parts)

    def post_process(self, ctx: AgentContext, raw_text: str) -> Optional[AgentOpinion]:
        parsed = try_parse_json(raw_text)
        if parsed is None:
            logger.warning("[BearAgent] failed to parse debate position JSON")
            return None

        # Store debate position in context
        ctx.set_data("bear_argument", parsed)

        return AgentOpinion(
            agent_name=self.agent_name,
            signal="sell" if parsed.get("conviction", 0) >= 60 else "hold",
            confidence=parsed.get("conviction", 50) / 100.0,
            reasoning=parsed.get("thesis", ""),
            raw_data=parsed,
        )
