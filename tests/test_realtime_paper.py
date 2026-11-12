"""Tests for real-time paper trading (research/realtime_paper.py)."""
import importlib.util
import sys
from argparse import Namespace
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent / "research"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("realtime_paper", ROOT / "realtime_paper.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

DAY = "2026-11-10"


def bars(closes, start="09:30", width="5min"):
    idx = pd.date_range(f"{DAY} {start}", periods=len(closes), freq=width, tz=rt.NY)
    return pd.DataFrame({"open": 700.0, "high": [max(700.5, c) for c in closes],
                         "low": [min(699.5, c) for c in closes], "close": closes}, index=idx)


def at(hhmm):
    return pd.Timestamp(f"{DAY} {hhmm}", tz=rt.NY)


def test_signal_waits_for_the_bar_to_close_and_matches_the_after_the_fact_rule():
    b = bars([700.0, 701.0, 699.0])                  # 9:35 bar closes above the 9:30 bar's high
    assert rt.check_signal(b, at("09:39:59"))["state"] == "wait"
    s = rt.check_signal(b, at("09:40:00"))
    assert s["state"] == "signal" and s["side"] == "long" and s["entry_time"] == "09:40"
    yesterday = b.copy()
    yesterday.index = yesterday.index - pd.Timedelta(days=1)
    assert rt.check_signal(yesterday, at("08:55"))["state"] == "wait"   # before the open: yesterday's bars don't count
    quiet = bars([700.0] * 30)                       # never leaves the range
    assert rt.check_signal(quiet, at("11:00"))["state"] == "wait"
    assert rt.check_signal(quiet, at("11:31"))["state"] == "none"


def test_stop_watch_uses_any_touch_after_entry():
    m = bars([700.0, 699.0, 696.5], start="09:40", width="1min")
    m.loc[m.index[2], "low"] = 696.4
    assert rt.stop_hit(m, "long", 696.5).name == m.index[2]
    assert rt.stop_hit(m, "short", 702.0) is None


def test_entry_buys_what_1000_dollars_allows_and_exit_scores_at_the_bid(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "LOG", tmp_path / "rt.csv")
    monkeypatch.setattr(rt, "now_et", lambda: at("09:40:05"))
    rt.log(Namespace(event="entry", side="long", contract="11/11 710C", ask=0.91, bid=0.89, qqq=701.0,
                     reason=None, note=""))
    with pytest.raises(SystemExit):                  # one trade a day
        rt.log(Namespace(event="entry", side="long", contract="11/11 711C", ask=0.80, bid=0.78, qqq=701.0,
                         reason=None, note=""))
    rt.log(Namespace(event="exit", side=None, contract=None, ask=1.20, bid=1.18, qqq=703.0, reason="trail", note=""))
    t = rt.trades(rt.read_log()).iloc[0]
    assert t.contracts == 10                          # $1,000 / $91
    assert t.per_contract == round((1.18 - 0.91) * 100 - 0.09, 2) and t.pnl == round(t.per_contract * 10, 2)
    with pytest.raises(SystemExit):                  # over the price cap
        rt.contracts_for(10_000, 1.05)


def _day(monkeypatch, tmp_path, day, hhmm="09:40:05"):
    monkeypatch.setattr(rt, "LOG", tmp_path / "rt.csv")
    monkeypatch.setattr(rt, "now_et", lambda: pd.Timestamp(f"{day} {hhmm}", tz=rt.NY))


def _entry(ask=0.92):
    rt.log(Namespace(event="entry", side="long", contract="11/17 700C", ask=ask, bid=ask - 0.02, qqq=686.0,
                     reason=None, note=""))


def _exit(event, reason, bid):
    rt.log(Namespace(event=event, side=None, contract=None, ask=bid + 0.02, bid=bid, qqq=690.0, reason=reason,
                     note=""))


def test_shadow_splits_off_only_after_a_trail_exit(tmp_path, monkeypatch):
    _day(monkeypatch, tmp_path, "2026-11-16")
    _entry()
    with pytest.raises(SystemExit):                  # nothing to split from before the official exit
        _exit("shadow_exit", "target", 1.84)
    _exit("exit", "trail", 1.11)
    t = rt.trades(rt.read_log()).iloc[0]
    assert pd.isna(t.get("shadow_pnl"))              # pending until the shadow's own exit
    with pytest.raises(SystemExit):                  # the shadow has no trail
        _exit("shadow_exit", "trail", 1.20)
    _exit("shadow_exit", "target", 1.84)             # the 2x target as a resting limit
    t = rt.trades(rt.read_log()).iloc[0]
    assert t.pnl == round(((1.11 - 0.92) * 100 - 0.09) * 10, 2)
    assert t.shadow_reason == "target" and t.shadow_pnl == round(((1.84 - 0.92) * 100 - 0.09) * 10, 2)
    with pytest.raises(SystemExit):                  # one shadow exit a day
        _exit("shadow_exit", "time", 1.50)


def test_shadow_copies_the_official_exit_when_the_trail_did_not_fire(tmp_path, monkeypatch):
    _day(monkeypatch, tmp_path, "2026-11-17")
    _entry(ask=0.95)
    _exit("exit", "stop", 0.35)
    with pytest.raises(SystemExit):                  # no trail, so no separate shadow exit
        _exit("shadow_exit", "stop", 0.35)
    t = rt.trades(rt.read_log()).iloc[0]
    assert t.shadow_reason == "stop" and t.shadow_pnl == t.pnl


def test_shadow_report_counts_only_trades_from_its_start_date(tmp_path, monkeypatch, capsys):
    _day(monkeypatch, tmp_path, "2026-11-12")
    _entry()
    _exit("exit", "trail", 1.11)                     # the trade that prompted the test: not counted
    _day(monkeypatch, tmp_path, "2026-11-16")
    _entry()
    _exit("exit", "target", 1.84)
    rt.report(Namespace())
    out = capsys.readouterr().out
    rows = out.split("No-trail shadow")[1].split("\n", 1)[1]   # the table, after the header line
    assert "2026-11-12" not in rows and "2026-11-16" in rows
    assert "1 trades: official $+919.10, shadow $+919.10" in rows
