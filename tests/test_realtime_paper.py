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


def test_an_empty_chart_at_the_open_means_no_bars_yet_not_a_crash():
    """2026-11-16 09:30:04: Yahoo's chart for the new session came back with an empty quote and the watcher crashed."""
    for payload in ({"chart": {"result": [{"indicators": {"quote": [{}]}}]}},
                    {"chart": {"result": [{"timestamp": [], "indicators": {"quote": [{"open": []}]}}]}}):
        b = rt.parse_chart(payload)
        assert b.empty
        assert rt.check_signal(b, at("09:30:05"))["state"] == "wait"
    ok = rt.parse_chart({"chart": {"result": [{"timestamp": [1794835800],
                                                "indicators": {"quote": [{"open": [1.0], "high": [2.0], "low": [0.5],
                                                                          "close": [1.5]}]}}]}})
    assert len(ok) == 1 and ok.close.iat[0] == 1.5


def test_the_cap_holds_after_losses_from_the_users_change_and_still_rises_on_new_highs():
    """The user, 2026-11-16: "Don't drop the cap"."""
    from paper_account import cap_balance
    book = pd.DataFrame({"date": ["2026-11-10", "2026-11-11", "2026-11-12", "2026-11-16"],
                         "pnl": [929.10, -621.81, 189.10, -558.81]})
    assert cap_balance(book, "2026-11-12") == pytest.approx(10_307.29)    # before the change: the balance itself
    assert cap_balance(book, "2026-11-16") == pytest.approx(10_496.39)    # the day of the change: unchanged
    assert cap_balance(book, "2026-11-17") == pytest.approx(10_496.39)    # after a loss: held, not 9,937.58
    up = pd.concat([book, pd.DataFrame({"date": ["2026-11-17"], "pnl": [900.0]})], ignore_index=True)
    assert cap_balance(up, "2026-11-18") == pytest.approx(10_837.58)      # a new high still raises it
    down = pd.concat([up, pd.DataFrame({"date": ["2026-11-18"], "pnl": [-600.0]})], ignore_index=True)
    assert cap_balance(down, "2026-11-19") == pytest.approx(10_837.58)    # and it holds there after the next loss


def test_after_a_loss_the_entry_still_takes_an_ask_up_to_the_held_cap(tmp_path, monkeypatch):
    _day(monkeypatch, tmp_path, "2026-11-16")
    rt.log(Namespace(event="entry", side="long", contract="11/17 688C", ask=0.99, bid=0.97, qqq=672.0,
                     reason=None, note=""))
    _exit("exit", "stop", 0.40)                       # a loss: the balance falls under $10,000
    _day(monkeypatch, tmp_path, "2026-11-17")
    _entry(ask=0.99)                                  # 1% of $10,000 / 100 = 0.99 still fits
    assert rt.trades(rt.read_log()).iloc[-1].contracts == 10


def test_a_breakeven_exit_splits_the_shadow_off_like_a_trail_exit(tmp_path, monkeypatch):
    _day(monkeypatch, tmp_path, "2026-11-17")
    _entry(ask=0.92)
    _exit("exit", "breakeven", 0.92)                 # ran past 1.15 (1.25x), came back to the entry
    assert pd.isna(rt.trades(rt.read_log()).iloc[0].get("shadow_pnl"))
    with pytest.raises(SystemExit):
        _exit("shadow_exit", "breakeven", 0.92)      # the shadow has no breakeven stop
    _exit("shadow_exit", "time", 1.40)
    t = rt.trades(rt.read_log()).iloc[0]
    assert t.pnl == round(-0.09 * 10, 2) and t.shadow_reason == "time"
