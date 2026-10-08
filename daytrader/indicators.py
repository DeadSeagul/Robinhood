"""Point-in-time indicators. Every function only uses bars up to and including the one it is given."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd


def session_vwap(day: pd.DataFrame) -> pd.Series:
    """Cumulative VWAP from the open, using each bar's typical price. Value at bar i uses bars <= i."""
    tp = (day.high + day.low + day.close) / 3
    vol = day.volume.replace(0, np.nan)
    cum_v = vol.cumsum().ffill()
    vwap = (tp * vol).cumsum().ffill() / cum_v
    return vwap.fillna(tp)


@dataclass(frozen=True)
class OpeningRange:
    high: float
    low: float
    volume: float
    complete_at: pd.Timestamp  # the time the last bar of the range finishes

    @property
    def width(self) -> float:
        return self.high - self.low


def opening_range(day: pd.DataFrame, minutes: int, bar_minutes: int = 5) -> OpeningRange | None:
    if day.empty:
        return None
    start = day.index[0].normalize() + pd.Timedelta(hours=9, minutes=30)
    end = start + pd.Timedelta(minutes=minutes)
    window = day[(day.index >= start) & (day.index < end)]
    if len(window) < minutes // bar_minutes:
        return None  # missing opening bars; do not trade on a partial range
    return OpeningRange(float(window.high.max()), float(window.low.min()), float(window.volume.sum()), end)


def window_volume(day: pd.DataFrame, minutes: int) -> float | None:
    start = day.index[0].normalize() + pd.Timedelta(hours=9, minutes=30)
    w = day[(day.index >= start) & (day.index < start + pd.Timedelta(minutes=minutes))]
    return float(w.volume.sum()) if len(w) else None


def relative_opening_volume(today: pd.DataFrame, prior_days: list[pd.DataFrame], minutes: int) -> float | None:
    """Today's volume in the first `minutes` vs the average of the same window over prior sessions."""
    now = window_volume(today, minutes)
    past = [v for v in (window_volume(d, minutes) for d in prior_days if not d.empty) if v]
    if now is None or not past:
        return None
    return now / float(np.mean(past))


def bar_time(ts: pd.Timestamp) -> time:
    return ts.time()
