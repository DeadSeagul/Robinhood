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
