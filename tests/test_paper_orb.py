"""Tests for the paper ORB scorer (research/paper_orb.py)."""
import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("paper_orb", Path(__file__).parent.parent / "research" / "paper_orb.py")
paper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper)


def day(rows):
    idx = pd.date_range("2026-10-16 09:30", periods=len(rows), freq="5min", tz="America/New_York")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def test_first_close_beyond_the_range_is_the_signal():
    d = day([[100, 101, 99, 100], [100, 100.9, 99.5, 100.5], [100.5, 101.6, 100.4, 101.5], [101.5, 102, 101, 101.8]])
    sig = paper.signal(d)
    assert sig["side"] == 1 and sig["k"] == 2 and sig["signal_time"] == "09:45"


def test_no_signal_after_11_25():
    rows = [[100, 101, 99, 100]] + [[100, 100.5, 99.5, 100]] * 30 + [[100, 102, 100, 101.5]]
    assert paper.signal(day(rows))["k"] is None


def test_share_trade_stops_at_the_other_side_of_the_range():
    d = day([[100, 101, 99, 100], [100, 101.2, 100, 101.1], [101.2, 101.3, 98.8, 99.0]])
    res = paper.share_trade(d, paper.signal(d))
    assert res["share_reason"] == "stop" and res["share_r"] == -1.0


def test_option_exits_at_the_stop_before_the_target_in_the_same_bar():
    d = day([[0.20, 0.50, 0.10, 0.30]])
    res = paper.option_trade(d, d.index[0])
    assert res["opt_reason"] == "stop"
