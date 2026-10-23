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


def test_qqq_stop_ignores_a_premium_drop_while_qqq_holds():
    opt = day([[0.19, 0.19, 0.11, 0.12], [0.12, 0.14, 0.11, 0.13]] + [[0.13, 0.15, 0.12, 0.14]] * 20)
    und = day([[704.4, 704.6, 703.8, 704.0]] * 22)  # long, share stop 701.37: never touched
    old = paper.option_trade(opt, opt.index[0])
    new = paper.option_trade(opt, opt.index[0], und=und, side=1, und_stop=701.37)
    assert old["opt_reason"] == "stop" and new["opt_reason"] == "time"


def test_qqq_stop_sells_at_the_option_bar_low_when_qqq_breaks_the_stop():
    opt = day([[0.19, 0.21, 0.17, 0.18], [0.18, 0.18, 0.09, 0.10]])
    und = day([[712.2, 712.6, 711.5, 712.1], [712.1, 714.9, 712.0, 714.8]])  # short, share stop 714.74
    res = paper.option_trade(opt, opt.index[0], und=und, side=-1, und_stop=714.74)
    assert res["opt_reason"] == "stop" and res["opt_exit"] == 0.09
