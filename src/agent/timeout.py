# -*- coding: utf-8 -*-
"""
Shared timeout helpers — used by runner, research, and orchestrator.
"""

from __future__ import annotations

import time
from typing import Optional


def remaining_timeout_seconds(
    start_time: float,
    max_seconds: Optional[float],
) -> Optional[float]:
    """Return remaining budget in seconds, or None when disabled.

    Uses ``time.monotonic()`` for clock-stable measurement (immune to NTP
    adjustments and daylight-saving shifts).
    """
    if max_seconds is None:
        return None
    return max(0.0, float(max_seconds) - (time.monotonic() - start_time))


def is_timed_out(
    start_time: float,
    max_seconds: Optional[float],
) -> bool:
    """Return whether the deadline has been exceeded."""
    remaining = remaining_timeout_seconds(start_time, max_seconds)
    return remaining is not None and remaining <= 0
