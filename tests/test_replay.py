"""Tests for the blind chart-replay drill (research/replay.py)."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("replay", Path(__file__).parent.parent / "research" / "replay.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def bars(rows, start="2026-08-03 10:00"):
    idx = pd.date_range(start, periods=len(rows), freq="5min", tz="America/New_York")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx).assign(volume=1000)


def make_days(n=8, after=None):
    """n flat sessions around $100; on the last day every bar after 10:30 trades at `after`."""
    days = {}
    for k in range(n):
        idx = pd.date_range(f"2026-08-{3 + k:02d} 09:30", "2026-08-%02d 15:55" % (3 + k), freq="5min",
                            tz="America/New_York")
        df = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.2, "volume": 1000}, index=idx)
        if after is not None and k == n - 1:
            df.loc[df.index > idx[12], ["open", "high", "low", "close"]] = after
        days[idx[0].date()] = df
    return days


def test_long_hits_target():
    res = replay.simulate(bars([[100, 100.4, 99.9, 100.3], [100.3, 101.2, 100.2, 101.0]]), 1, 99.5, 101.0, 60)
    assert res["reason"] == "target"
    assert res["r"] == pytest.approx((1.0 - 0.02) / 0.5, rel=1e-3)


def test_stop_counts_first_when_one_bar_touches_both():
    res = replay.simulate(bars([[100, 101.5, 99.0, 100.0]]), 1, 99.5, 101.0, 60)
    assert res["reason"] == "stop"
    assert res["r"] < -1


def test_short_mirrors_long():
    res = replay.simulate(bars([[100, 100.1, 98.9, 99.0]]), -1, 100.5, 99.0, 60)
    assert res["reason"] == "target" and res["r"] > 1.9


def test_open_past_the_stop_is_skipped():
    res = replay.simulate(bars([[99.0, 99.2, 98.8, 99.1]]), 1, 99.5, 101.0, 60)
    assert res["reason"].startswith("skipped") and res["r"] == 0


def test_time_stop_exits_at_the_close_of_the_last_bar():
    rows = [[100, 100.2, 99.9, 100.1]] * 3 + [[100.1, 100.3, 100.0, 100.25]]
    res = replay.simulate(bars(rows), 1, 99.0, 102.0, 20)
    assert res["reason"] == "time" and res["exit"] == 100.25


def test_render_never_shows_bars_after_the_decision_point():
    days = make_days(after=987.65)
    d = sorted(days)[-1]
    t = days[d].index[12]  # 10:30 bar
    text = replay.render("TEST", days, d, t)
    assert "987" not in text
    assert "10:30" in text and "10:35" in text  # last visible bar, and the "as of" time
    assert "10:40" not in text
