"""Tests for the pre-market news log (research/news_log.py)."""
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent / "research"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("news_log", ROOT / "news_log.py")
news_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(news_log)


def sessions(n=21, last_move=0.0, last_range=1.0):
    """n flat sessions with a 1.0 range around 100; the last one drifts by last_move with range last_range."""
    frames = []
    for k, day in enumerate(pd.bdate_range("2026-09-01", periods=n)):
        idx = pd.date_range(f"{day:%Y-%m-%d} 09:30", f"{day:%Y-%m-%d} 15:55", freq="5min", tz="America/New_York")
        last = k == n - 1
        close = 100 + (last_move * pd.Series(range(len(idx)), index=idx) / len(idx) if last else 0)
        half = (last_range if last else 1.0) / 2
        frames.append(pd.DataFrame({"open": 100.0, "high": 100 + half, "low": 100 - half, "close": close}, index=idx))
    return pd.concat(frames), f"{pd.bdate_range('2026-09-01', periods=n)[-1]:%Y-%m-%d}"


def test_entries_at_or_after_the_open_are_late():
    et = lambda s: pd.Timestamp(s, tz="America/New_York").to_pydatetime().astimezone(timezone.utc)
    assert not news_log.is_late("2026-10-23", et("2026-10-23 08:50"))
    assert news_log.is_late("2026-10-23", et("2026-10-23 09:30"))
    assert news_log.is_late("2026-10-23", et("2026-10-24 08:50"))
    assert not news_log.is_late("2026-10-23", datetime(2026, 10, 22, 23, 0, tzinfo=timezone.utc))


def test_direction_and_volatility_are_scored_on_the_morning_window():
    bars, day = sessions(last_move=2.0, last_range=3.0)
    res = news_log.score_day(bars, day, "up", "high")
    assert res["move_pct"] > 0 and res["bias_hit"] == 1.0
    assert res["base_range_pct"] == 1.0 and res["vol_hit"] == 1.0
    res = news_log.score_day(bars, day, "down", "normal")
    assert res["bias_hit"] == 0.0 and res["vol_hit"] == 0.0
    assert pd.isna(news_log.score_day(bars, day, "none", "normal")["bias_hit"])


def test_binomial_p_value():
    assert news_log.binom_p(5, 10) == 1.0
    assert abs(news_log.binom_p(0, 5) - 2 / 32) < 1e-12
