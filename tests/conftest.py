import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NY = "America/New_York"


def day_index(d: date) -> pd.DatetimeIndex:
    start = pd.Timestamp(d).tz_localize(NY) + pd.Timedelta(hours=9, minutes=30)
    return pd.date_range(start, periods=78, freq="5min")


def bars_from_path(d: date, closes, volume=10_000, spread=0.05) -> pd.DataFrame:
    idx = day_index(d)
    closes = np.asarray(closes, dtype=float)
    opens = np.r_[closes[0], closes[:-1]]
    vol = np.full(len(idx), volume, dtype=float) if np.isscalar(volume) else np.asarray(volume, dtype=float)
    return pd.DataFrame({"open": opens, "high": np.maximum(opens, closes) + spread,
                         "low": np.minimum(opens, closes) - spread, "close": closes, "volume": vol}, index=idx)


def trading_days(n: int, start: date = date(2026, 3, 2)) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def breakout_day_path(base=100.0):
    """Opening range 99.5-101 for 15 min, breakout to 101.5, pullback to 101.1 holding, then rally."""
    p = [100.5, 101.0, 100.0]                     # 9:30, 9:35, 9:40  -> OR high ~101.05, low ~99.95
    p += [101.5]                                  # 9:45 breakout close above OR high
    p += [101.2]                                  # 9:50 pullback that holds above OR high
    p += [101.6, 102.0, 102.5, 103.0, 103.5, 104.0, 104.5, 105.0]
    p += [105.0] * (78 - len(p))
    return np.array(p) * base / 100.0


@pytest.fixture
def synthetic_market():
    """25 sessions: SPY/QQQ drift up gently; AAA is quiet except a high-volume breakout on the last day."""
    days = trading_days(25)
    rng = np.random.default_rng(3)
    intraday = {"SPY": [], "QQQ": [], "AAA": []}
    for i, d in enumerate(days):
        for s, b in (("SPY", 500.0), ("QQQ", 450.0)):
            path = b + np.cumsum(rng.normal(0.02, 0.05, 78)) + i
            intraday[s].append(bars_from_path(d, path, 200_000))
        if i == len(days) - 1:
            vol = np.full(78, 20_000.0)
            vol[:3] = 150_000                     # relative opening volume >> 2
            intraday["AAA"].append(bars_from_path(d, breakout_day_path(), vol))
        else:
            intraday["AAA"].append(bars_from_path(d, 100 + rng.normal(0, 0.1, 78), 20_000))
    intraday = {s: pd.concat(v) for s, v in intraday.items()}
    daily = {}
    for s, b in intraday.items():
        g = b.groupby(b.index.date)
        df = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                           "volume": g.volume.sum() * 40})   # scaled so average daily volume > 1M
        df.index = pd.DatetimeIndex(df.index)
        daily[s] = df
    return intraday, daily, days
