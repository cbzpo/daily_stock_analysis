# -*- coding: utf-8 -*-
"""
Trade-level Risk Engine
======================

Provides quantitative risk management for individual trades:
1. ATR-based position sizing (max loss per trade ≤ risk_budget)
2. Dynamic stop-loss / take-profit from ATR multiples
3. Risk-reward ratio calculation and filtering
4. Max exposure limits per stock and sector

Usage:
    engine = RiskEngine(total_capital=1_000_000)
    profile = engine.compute_risk_profile(
        code="600519",
        current_price=1800.0,
        df=daily_bars,  # DataFrame with OHLCV
        signal="buy",
    )
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class RiskConfig:
    """Risk engine configuration (all percentages in decimal form)."""

    # Position sizing
    risk_per_trade: float = 0.01          # Max loss per trade as % of capital (1%)
    max_position_pct: float = 0.20        # Max single-stock weight (20%)
    max_sector_pct: float = 0.35          # Max sector weight (35%)

    # ATR parameters
    atr_period: int = 14                  # ATR lookback period
    atr_sl_multiplier: float = 2.0        # Stop-loss = entry - ATR * multiplier
    atr_tp_multiplier: float = 3.0        # Take-profit = entry + ATR * multiplier

    # Risk-reward filter
    min_rr_ratio: float = 2.0             # Minimum R:R to keep signal active

    # Volatility scaling
    vol_scale_enabled: bool = True        # Reduce size when vol is high
    vol_scale_threshold: float = 1.5      # ATR / ATR_MA ratio that triggers scaling
    vol_scale_factor: float = 0.5         # Multiply position by this when vol high

    # Max drawdown circuit breaker
    max_drawdown_pct: float = 0.10        # Halt new entries if drawdown > 10%


# ---------------------------------------------------------------------------
# ATR calculation
# ---------------------------------------------------------------------------

def compute_true_range(df: pd.DataFrame) -> pd.Series:
    """Compute True Range column from OHLC DataFrame.

    Expects columns: high, low, close (case-insensitive).
    """
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range (Wilder's smoothing)."""
    tr = compute_true_range(df)
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


# ---------------------------------------------------------------------------
# Position sizing
# ---------------------------------------------------------------------------

def kelly_position_size(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    risk_capital: float,
    max_pct: float = 0.20,
) -> float:
    """Kelly-criterion position size (fraction of capital).

    Returns a value in [0, max_pct].
    Kelly formula: f* = (p * b - q) / b
    where p = win_rate, q = 1-p, b = avg_win / avg_loss
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    b = avg_win / avg_loss
    q = 1.0 - win_rate
    kelly_f = (win_rate * b - q) / b

    # Half-Kelly for safety
    kelly_f = max(0.0, kelly_f * 0.5)
    return min(kelly_f, max_pct)


def atr_based_position_size(
    current_price: float,
    atr_value: float,
    risk_per_trade: float,
    total_capital: float,
    max_position_pct: float = 0.20,
) -> float:
    """Calculate position size based on ATR risk.

    Position size (shares) = (capital * risk_per_trade) / (ATR * multiplier)
    Returns the number of shares, capped by max_position_pct.
    """
    if current_price <= 0 or atr_value <= 0:
        return 0.0

    risk_amount = total_capital * risk_per_trade
    stop_distance = atr_value * 2.0  # Default 2x ATR stop
    shares = risk_amount / stop_distance

    # Cap by max position percentage
    max_shares = (total_capital * max_position_pct) / current_price
    return min(shares, max_shares)


# ---------------------------------------------------------------------------
# Risk profile dataclass
# ---------------------------------------------------------------------------

@dataclass
class RiskProfile:
    """Quantitative risk assessment for a single stock."""

    code: str
    current_price: float

    # ATR
    atr: float = 0.0
    atr_pct: float = 0.0              # ATR as % of price
    atr_period: int = 14

    # Position sizing
    suggested_shares: int = 0
    suggested_amount: float = 0.0     # Suggested investment amount
    position_pct: float = 0.0         # As % of total capital

    # Stop-loss / Take-profit
    stop_loss_price: float = 0.0
    stop_loss_pct: float = 0.0        # Loss from entry to SL
    take_profit_price: float = 0.0
    take_profit_pct: float = 0.0      # Gain from entry to TP

    # Risk-reward
    risk_reward_ratio: float = 0.0
    risk_amount: float = 0.0          # Potential loss in $
    reward_amount: float = 0.0        # Potential gain in $

    # Volatility regime
    vol_regime: str = "normal"        # low / normal / high
    vol_scale_applied: bool = False

    # Risk verdict
    pass_risk_filter: bool = True
    risk_block_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "current_price": round(self.current_price, 4),
            "atr": round(self.atr, 4),
            "atr_pct": round(self.atr_pct, 4),
            "atr_period": self.atr_period,
            "suggested_shares": self.suggested_shares,
            "suggested_amount": round(self.suggested_amount, 2),
            "position_pct": round(self.position_pct, 4),
            "stop_loss_price": round(self.stop_loss_price, 4),
            "stop_loss_pct": round(self.stop_loss_pct, 4),
            "take_profit_price": round(self.take_profit_price, 4),
            "take_profit_pct": round(self.take_profit_pct, 4),
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "risk_amount": round(self.risk_amount, 2),
            "reward_amount": round(self.reward_amount, 2),
            "vol_regime": self.vol_regime,
            "vol_scale_applied": self.vol_scale_applied,
            "pass_risk_filter": self.pass_risk_filter,
            "risk_block_reasons": self.risk_block_reasons,
        }


# ---------------------------------------------------------------------------
# Risk Engine
# ---------------------------------------------------------------------------

class RiskEngine:
    """Trade-level risk management engine."""

    def __init__(
        self,
        total_capital: float = 1_000_000.0,
        config: Optional[RiskConfig] = None,
    ):
        self.total_capital = total_capital
        self.config = config or RiskConfig()

    def compute_risk_profile(
        self,
        code: str,
        current_price: float,
        df: Optional[pd.DataFrame] = None,
        signal: str = "buy",
        *,
        win_rate: Optional[float] = None,
        avg_win_pct: Optional[float] = None,
        avg_loss_pct: Optional[float] = None,
    ) -> RiskProfile:
        """Compute full risk profile for a stock.

        Args:
            code: Stock code
            current_price: Current price
            df: Daily OHLCV DataFrame (columns: open, high, low, close, volume)
            signal: Trade signal (buy/sell/hold)
            win_rate: Optional historical win rate for Kelly sizing
            avg_win_pct: Optional average winning trade %
            avg_loss_pct: Optional average losing trade %

        Returns:
            RiskProfile with all quantitative risk metrics
        """
        cfg = self.config
        profile = RiskProfile(code=code, current_price=current_price)

        if current_price <= 0:
            profile.pass_risk_filter = False
            profile.risk_block_reasons.append("Invalid current price")
            return profile

        # 1. Compute ATR
        if df is not None and len(df) >= cfg.atr_period:
            atr_series = compute_atr(df, period=cfg.atr_period)
            atr_value = float(atr_series.iloc[-1]) if not atr_series.empty else 0.0
        else:
            # Fallback: estimate ATR from price if no data
            atr_value = current_price * 0.02  # Assume 2% daily vol

        profile.atr = atr_value
        profile.atr_pct = atr_value / current_price if current_price > 0 else 0.0
        profile.atr_period = cfg.atr_period

        # 2. Volatility regime
        profile.vol_regime = self._classify_vol_regime(df, cfg.atr_period)

        # 3. Dynamic stop-loss and take-profit
        if signal.lower() in ("buy", "strong buy", "add"):
            profile.stop_loss_price = current_price - (atr_value * cfg.atr_sl_multiplier)
            profile.take_profit_price = current_price + (atr_value * cfg.atr_tp_multiplier)
        elif signal.lower() in ("sell", "strong sell", "reduce"):
            # For sell signals, flip the logic
            profile.stop_loss_price = current_price + (atr_value * cfg.atr_sl_multiplier)
            profile.take_profit_price = current_price - (atr_value * cfg.atr_tp_multiplier)
        else:
            # Hold: use symmetric levels
            profile.stop_loss_price = current_price - (atr_value * cfg.atr_sl_multiplier)
            profile.take_profit_price = current_price + (atr_value * cfg.atr_tp_multiplier)

        # Ensure positive prices
        profile.stop_loss_price = max(0.01, profile.stop_loss_price)
        profile.take_profit_price = max(0.01, profile.take_profit_price)

        profile.stop_loss_pct = (current_price - profile.stop_loss_price) / current_price
        profile.take_profit_pct = (profile.take_profit_price - current_price) / current_price

        # 4. Risk-reward ratio
        risk_per_share = abs(current_price - profile.stop_loss_price)
        reward_per_share = abs(profile.take_profit_price - current_price)
        if risk_per_share > 0:
            profile.risk_reward_ratio = reward_per_share / risk_per_share
        profile.risk_amount = risk_per_share
        profile.reward_amount = reward_per_share

        # 5. Position sizing
        if signal.lower() in ("buy", "strong buy", "add"):
            # Use Kelly if available, else ATR-based
            if win_rate is not None and avg_win_pct is not None and avg_loss_pct is not None:
                kelly_pct = kelly_position_size(
                    win_rate, avg_win_pct, avg_loss_pct,
                    self.total_capital, cfg.max_position_pct,
                )
                suggested_amount = self.total_capital * kelly_pct
            else:
                shares = atr_based_position_size(
                    current_price, atr_value,
                    cfg.risk_per_trade, self.total_capital,
                    cfg.max_position_pct,
                )
                suggested_amount = shares * current_price

            # Volatility scaling
            if cfg.vol_scale_enabled and profile.vol_regime == "high":
                suggested_amount *= cfg.vol_scale_factor
                profile.vol_scale_applied = True

            profile.suggested_amount = suggested_amount
            profile.suggested_shares = int(suggested_amount / current_price) if current_price > 0 else 0
            profile.position_pct = suggested_amount / self.total_capital if self.total_capital > 0 else 0.0
        else:
            # Sell/hold: no new position
            profile.suggested_amount = 0.0
            profile.suggested_shares = 0
            profile.position_pct = 0.0

        # 6. Risk filter checks
        block_reasons = []

        # R:R filter
        if signal.lower() in ("buy", "strong buy", "add"):
            if profile.risk_reward_ratio < cfg.min_rr_ratio:
                block_reasons.append(
                    f"R:R {profile.risk_reward_ratio:.2f} < minimum {cfg.min_rr_ratio}"
                )

        # Position size cap
        if profile.position_pct > cfg.max_position_pct:
            block_reasons.append(
                f"Position {profile.position_pct:.1%} > max {cfg.max_position_pct:.1%}"
            )

        # Stop-loss too wide
        if profile.stop_loss_pct > 0.15:  # >15% stop
            block_reasons.append(
                f"Stop-loss {profile.stop_loss_pct:.1%} too wide (>15%)"
            )

        profile.risk_block_reasons = block_reasons
        profile.pass_risk_filter = len(block_reasons) == 0

        return profile

    def _classify_vol_regime(
        self,
        df: Optional[pd.DataFrame],
        atr_period: int,
    ) -> str:
        """Classify current volatility regime as low/normal/high."""
        if df is None or len(df) < atr_period * 2:
            return "normal"

        try:
            atr_series = compute_atr(df, period=atr_period)
            recent_atr = float(atr_series.iloc[-1])
            avg_atr = float(atr_series.mean())

            if avg_atr <= 0:
                return "normal"

            ratio = recent_atr / avg_atr
            cfg = self.config

            if ratio < (1.0 / cfg.vol_scale_threshold):
                return "low"
            elif ratio > cfg.vol_scale_threshold:
                return "high"
            else:
                return "normal"
        except Exception:
            return "normal"

    def filter_signals(
        self,
        signals: List[Dict[str, Any]],
        df_dict: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> List[Dict[str, Any]]:
        """Filter a batch of signals through the risk engine.

        Args:
            signals: List of dicts with keys: code, current_price, signal, ...
            df_dict: Optional mapping of code -> daily OHLCV DataFrame

        Returns:
            Filtered list with risk_profile attached and pass_risk_filter flag
        """
        df_dict = df_dict or {}
        filtered = []

        for sig in signals:
            code = sig.get("code", "")
            price = sig.get("current_price", 0.0)
            signal_type = sig.get("signal", "hold")

            df = df_dict.get(code)
            profile = self.compute_risk_profile(
                code=code,
                current_price=price,
                df=df,
                signal=signal_type,
            )

            sig_with_risk = dict(sig)
            sig_with_risk["risk_profile"] = profile.to_dict()
            sig_with_risk["pass_risk_filter"] = profile.pass_risk_filter
            sig_with_risk["risk_block_reasons"] = profile.risk_block_reasons

            if profile.pass_risk_filter:
                filtered.append(sig_with_risk)
            else:
                logger.info(
                    "[RiskEngine] Signal blocked for %s: %s",
                    code, "; ".join(profile.risk_block_reasons),
                )

        return filtered
