"""Tests for the 30-year daily study (research/history30)."""
import datetime as dt
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent / "research" / "history30"
sys.path.insert(0, str(ROOT))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cal = load("build_calendar")
study = load("study")


def test_last_day_handles_ranges_across_months():
    assert cal.last_day(2026, "January", "27-28") == dt.date(2026, 1, 28)
    assert cal.last_day(2013, "April/May", "30-1") == dt.date(2013, 5, 1)
    assert cal.last_day(2017, "Jan/Feb", "31-1") == dt.date(2017, 2, 1)
    assert cal.last_day(2023, "October", "31-1") == dt.date(2023, 11, 1)  # page names only the first month
    assert cal.last_day(1998, "June July", "30 1") == dt.date(1998, 7, 1)


def test_parse_historical_keeps_scheduled_meetings_only():
    page = "".join(f"<h5 class='x'>{h}</h5>" for h in [
        "January 28-29 Meeting - 2020", "March 2 (unscheduled) Meeting - 2020", "March 15 (unscheduled) Meeting - 2020",
        "March 17-18 (cancelled) Meeting - 2020", "March 19 (notation vote) - 2020", "April 8 Conference Call - 2020",
        "June 30-July 1 Meeting - 2020", "July 31-August 1  Meeting - 2020", "Oct/Nov 31-1 Meeting - 2020",
        "May 5 Meeting - 2019"])
    assert cal.parse_historical(page, 2020) == [dt.date(2020, 1, 29), dt.date(2020, 7, 1), dt.date(2020, 8, 1),
                                                dt.date(2020, 11, 1)]


def test_parse_current_skips_notation_votes():
    cell = ('<div class="fomc-meeting__month col"><strong>{m}</strong></div>'
            '<div class="fomc-meeting__date col">{d}</div>')
    page = ('<h4><a id="1">2025 FOMC Meetings</a></h4>' + cell.format(m="January", d="28-29")
            + cell.format(m="August", d="22 (notation vote)") + cell.format(m="December", d="9-10*"))
    assert cal.parse_current(page) == [dt.date(2025, 1, 29), dt.date(2025, 12, 10)]


def test_split_meeting_keeps_the_later_day():
    days = [dt.date(2003, 8, 12), dt.date(2003, 9, 15), dt.date(2003, 9, 16), dt.date(2003, 10, 28)]
    assert cal.merge_split_meetings(days) == [dt.date(2003, 8, 12), dt.date(2003, 9, 16), dt.date(2003, 10, 28)]


def frame(ranges, opens_eq_prev=False):
    """Daily bars around 100 with the given high-low ranges (as fractions of 100)."""
    idx = pd.bdate_range("2020-01-01", periods=len(ranges))
    close = pd.Series(100.0, index=idx)
    df = pd.DataFrame({"open": 100.5, "high": 100 + 100 * np.array(ranges), "low": 100.0, "close": close})
    if opens_eq_prev:
        df["open"] = 100.0
    return df.set_index(idx)


def test_big_day_baseline_uses_only_earlier_days():
    f = study.features(frame([0.01] * 22 + [0.02]))
    last = f.iloc[-1]
    assert abs(last.base - 0.01) < 1e-12  # today's 2% range isn't in its own baseline
    assert last.big == 1.0
    # Row 0 has no prior close, so the first full 20-day baseline is at row 21.
    assert np.isnan(f.big.iloc[20]) and f.big.iloc[21] == 0.0
    assert f.prior_big.iloc[-1] == 0.0


def test_open_check_flags_years_with_copied_opens():
    f = study.features(frame([0.01] * 30, opens_eq_prev=True))
    share, ok = study.usable_open_years(f)
    assert share.iloc[0] > 0.9 and ok == set()
    f2 = study.features(frame([0.01] * 30))
    assert study.usable_open_years(f2)[1] == {2020}


def test_rule_and_scoring():
    d = pd.DataFrame({"prior_big": [1.0, 0.0, 0.0, 0.0], "gap": [0.0, 0.012, -0.002, 0.0],
                      "any_event": [False, False, False, True]})
    assert study.rule(d).tolist() == [True, True, False, True]
    r = study.score_rule(d, study.rule(d), pd.Series([True, False, False, False]))
    assert r["rule accuracy"] == "50%" and r["'always normal' accuracy"] == "75%" and r["big days caught"] == "100%"


orb10 = load("orb10")


def test_pick_strike_walks_out_of_the_money_until_under_cap():
    ts = pd.Timestamp("2026-11-18 10:00", tz="America/New_York")
    k, mid = orb10.pick_strike(660.0, ts, 0.25, True, 1.0)
    assert k > 660 and mid + orb10.HALF_SPREAD <= 1.0
    # one strike nearer the money is over the cap
    t = orb10.years_left(ts, 1)
    assert orb10.bs(660.0, k - 1, t, 0.25, True) + orb10.HALF_SPREAD > 1.0
    kp, _ = orb10.pick_strike(660.0, ts, 0.25, False, 1.0)
    assert kp < 660


def test_option_bars_use_the_favorable_extreme_for_the_high():
    idx = pd.date_range("2026-11-18 10:00", periods=2, freq="5min", tz="America/New_York")
    day = pd.DataFrame({"open": [660.0, 661.0], "high": [662.0, 663.0], "low": [658.0, 659.0], "close": [661.0, 662.0]},
                       index=idx)
    c = orb10.option_bars(day, idx[0], 665, 0.25, True)
    p = orb10.option_bars(day, idx[0], 655, 0.25, False)
    assert (c.high >= c.open).all() and (c.low <= c.open).all()
    assert (p.high >= p.open).all() and (p.low <= p.open).all()
    assert c.high.iat[0] > c.low.iat[0] and p.high.iat[0] > p.low.iat[0]


s20 = load("strategies20")


def daily_frame(n=70, start="2026-01-01"):
    idx = pd.bdate_range(start, periods=n)
    close = pd.Series(100 + np.arange(n, dtype=float), index=idx)
    return pd.DataFrame({"open": close - 0.5, "high": close + 1, "low": close - 1, "close": close, "div": 0.0}, index=idx)


def test_turn_of_month_holds_last_day_through_third_day():
    df = daily_frame()
    on, dp = s20.exposures(df)["D7"]
    feb = df.index[(df.index.month == 2)]
    jan_last = df.index[df.index.month == 1][-1]
    assert dp[jan_last] == 1 and on[jan_last] == 0          # bought at the open of the last day
    assert list(dp[feb[:4]]) == [1, 1, 1, 0]                 # held through the 3rd trading day
    assert list(on[feb[:4]]) == [1, 1, 1, 0]                 # nights into days 1-3 held, not into day 4
    g, n, turns = s20.daily_returns(df, on, dp)
    assert turns[jan_last] == 1 and turns[feb[2]] == 1       # one buy, one sell


def test_overnight_and_daytime_split_buy_and_hold():
    df = daily_frame()
    df.loc[df.index[30], "div"] = 0.4
    ex = s20.exposures(df)
    g0 = s20.daily_returns(df, *ex["D0"])[0]
    g8 = s20.daily_returns(df, *ex["D8"])[0]
    g9 = s20.daily_returns(df, *ex["D9"])[0]
    assert np.allclose(((1 + g8) * (1 + g9)).iloc[1:], (1 + g0).iloc[1:])
    assert g8.iloc[30] > g8.iloc[29]                         # the dividend lands in the overnight return
    n8, t8 = s20.daily_returns(df, *ex["D8"])[1:]
    assert t8.iloc[5] == 2                                   # buy at the close, sell at the open: two trades a day


def test_signal_trades_at_the_next_open():
    df = daily_frame(10)
    s = pd.Series([0, 0, 1, 1, 0, 0, 0, 0, 0, 0], index=df.index)
    dp = s.shift(1).fillna(0)
    on = dp.shift(1).fillna(0)
    assert list(dp) == [0, 0, 0, 1, 1, 0, 0, 0, 0, 0]
    assert list(on) == [0, 0, 0, 0, 1, 1, 0, 0, 0, 0]       # held overnight, sold at the next open


def test_stateful_entry_and_exit():
    e = pd.Series([0, 1, 0, 0, 1, 0])
    x = pd.Series([0, 0, 0, 1, 0, 1])
    assert list(s20.stateful(e, x)) == [0, 1, 1, 0, 1, 0]


def test_walk_counts_stop_first():
    idx = pd.date_range("2026-11-18 09:30", periods=3, freq="5min", tz="America/New_York")
    g = pd.DataFrame({"open": [100, 100, 100], "high": [101, 103, 100], "low": [99, 97, 99], "close": [100, 100, 100]}, index=idx)
    assert s20.walk(g, 1, 1, 100, 98, 102, "16:00") == (98, "stop")
    assert s20.walk(g, 2, 1, 100, 98, 102, "16:00") == (100, "time")


osym = load("orb_symbols")


def test_stock_in_play_uses_prior_sessions_only():
    days = {}
    for s in osym.STOCKS:
        days[s] = {}
        for i, d in enumerate(pd.bdate_range("2026-01-05", periods=16)):
            idx = pd.date_range(f"{d:%Y-%m-%d} 09:30", periods=2, freq="5min", tz="America/New_York")
            vol = 1000.0
            if s == "TSLA" and i == 15:
                vol = 5000.0          # TSLA's opening volume is 5x its usual on the last day
            if s == "AAPL" and i == 15:
                vol = 3000.0
            days[s][pd.Timestamp(d)] = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": [vol, 1.0]}, index=idx)
    pick, frame = osym.in_play(days)
    last = max(pick.index)
    assert pick[last] == "TSLA" and abs(frame.loc[last, "TSLA"] - 5.0) < 1e-9
    assert pick.index.min() == pd.Timestamp(pd.bdate_range("2026-01-05", periods=16)[14])  # needs 14 earlier sessions
