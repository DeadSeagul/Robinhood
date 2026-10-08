from datetime import date, time

import pandas as pd
import pytest
from conftest import bars_from_path, breakout_day_path

from daytrader.broker.sim import SimBroker
from daytrader.config import AppConfig, CostConfig, LiveTradingDisabled, RiskConfig, StrategyConfig, check_mode
from daytrader.indicators import opening_range, relative_opening_volume, session_vwap
from daytrader.risk import DayRisk, position_size
from daytrader.strategy import DayContext, EntrySignal, OrbStrategy

D = date(2026, 3, 2)
NOCOST = CostConfig(min_half_spread=0, half_spread_bps=0, slippage_bps=0, sec_fee_per_dollar=0, taf_per_share=0,
                    reject_probability=0, max_fill_volume_fraction=1.0)


# --- config / safety ------------------------------------------------------------------------
def test_only_paper_and_backtest_modes_allowed():
    assert check_mode("paper") == "paper"
    for bad in ("live", "LIVE", "real", ""):
        with pytest.raises(LiveTradingDisabled):
            check_mode(bad)
    with pytest.raises(LiveTradingDisabled):
        AppConfig(mode="live")


def test_options_and_shorting_rejected():
    with pytest.raises(ValueError):
        AppConfig(mode="paper", risk=RiskConfig(allow_options=True))
    with pytest.raises(ValueError):
        AppConfig(mode="paper", risk=RiskConfig(allow_short=True))


# --- indicators -------------------------------------------------------------------------------
def test_vwap_is_cumulative_and_point_in_time():
    df = bars_from_path(D, [10, 11, 12] + [12] * 75, volume=[100, 300, 600] + [1] * 75, spread=0)
    v = session_vwap(df)
    assert v.iloc[0] == pytest.approx(10)
    tp1 = (11 + 10 + 11) / 3                                                     # (high + low + close) / 3
    assert v.iloc[1] == pytest.approx((10 * 100 + tp1 * 300) / 400)
    df2 = df.copy()
    df2.iloc[5:, df2.columns.get_loc("close")] = 999.0                         # change the future...
    assert session_vwap(df2).iloc[:5].tolist() == pytest.approx(v.iloc[:5].tolist())  # ...past unchanged


def test_opening_range_and_relative_volume():
    df = bars_from_path(D, breakout_day_path(), volume=[300, 300, 300] + [10] * 75)
    o = opening_range(df, 15)
    assert o.high == pytest.approx(101.05) and o.low == pytest.approx(99.95)
    assert o.complete_at.time() == time(9, 45)
    quiet = bars_from_path(D, breakout_day_path(), volume=100)
    assert relative_opening_volume(df, [quiet, quiet], 15) == pytest.approx(3.0)
    assert opening_range(df.iloc[:2], 15) is None   # partial range is never traded


# --- risk -----------------------------------------------------------------------------------
def test_position_size_respects_risk_and_cash():
    r = RiskConfig(starting_equity=25_000)
    qty, why = position_size(100.0, 99.0, 25_000, 25_000, r, NOCOST)
    assert qty == 62 and why == "risk-limited"                          # $62.50 budget / $1 risk
    qty, why = position_size(100.0, 99.99, 25_000, 1_000, r, NOCOST)
    assert qty == 9 and why == "cash-limited"                           # no leverage
    assert position_size(100.0, 100.0, 25_000, 25_000, r, NOCOST)[0] == 0
    assert position_size(500.0, 400.0, 68, 68, r, NOCOST)[0] == 0      # tiny account sizes to zero


def test_daily_loss_limit_and_entry_cap():
    dr = DayRisk(10_000, RiskConfig())
    assert dr.can_enter(10_000, 50)[0]
    assert dr.can_enter(9_960, 50)[0]                     # 40 lost + 50 at risk = 90 <= 100 limit
    assert not dr.can_enter(9_940, 50)[0]                 # 60 lost + 50 at risk > 100 limit
    assert dr.check(9_899) and dr.halted
    dr2 = DayRisk(10_000, RiskConfig(), entries=2)
    assert "max 2 entries" in dr2.can_enter(10_000, 10)[1]


# --- strategy state machine -----------------------------------------------------------------
def run_strategy(path, cfg=StrategyConfig(), market_ok=True, prior_high=None, volume=10_000):
    df = bars_from_path(D, path, volume)
    o = opening_range(df, cfg.opening_range_minutes)
    st = OrbStrategy(cfg, DayContext("AAA", prior_high, None, float(df.open.iloc[0])), o)
    vw = session_vwap(df)
    sigs = []
    for ts, bar in df.iterrows():
        s = st.on_bar(ts, bar, float(vw.loc[ts]), market_ok)
        if s:
            sigs.append(s)
            st.on_order_dead()
    return st, sigs, o


def test_breakout_then_retest_produces_buy_stop():
    st, sigs, o = run_strategy(breakout_day_path())
    s = sigs[0]
    assert s.order_type == "stop" and s.created_at.time() == time(9, 55)  # retest bar 9:50 completes at 9:55
    assert s.trigger == pytest.approx(101.5 + 0.05 + 0.01)                # retest bar high + 1 tick
    assert s.stop_loss < s.trigger and s.target(s.trigger) == pytest.approx(s.trigger + 2 * s.risk_per_share)
    assert s.expires_at.time() == time(10, 5)


def test_no_signal_when_market_below_vwap_or_inside_range():
    assert run_strategy(breakout_day_path(), market_ok=False)[1] == []
    flat = [100.5, 101.0, 100.0] + [100.5] * 75
    assert run_strategy(flat)[1] == []


def test_failed_breakout_resets():
    p = [100.5, 101.0, 100.0, 101.5, 100.5] + [100.5] * 73   # breaks out, then closes back inside
    st, sigs, _ = run_strategy(p)
    assert sigs == []
    assert any("breakout failed" in r.reason for r in st.rejections)


def test_reward_risk_rejection_at_prior_day_high():
    st, sigs, _ = run_strategy(breakout_day_path(), prior_high=101.9)
    assert sigs == [] or sigs[0].created_at.time() > time(9, 55)
    assert any("reward/risk" in r.reason for r in st.rejections)


def test_no_new_signals_after_entry_window():
    late = [100.5, 101.0, 100.0] + [100.5] * 20 + [101.5, 101.2] + [102] * 53   # breakout at 11:25
    assert run_strategy(late)[1] == []


# --- simulated broker -------------------------------------------------------------------------
def make_signal(trigger=101.0, stop=100.0, target_r=2.0, otype="stop"):
    t0 = pd.Timestamp("2026-03-02 09:55", tz="America/New_York")
    return EntrySignal("AAA", t0, otype, trigger, stop, target_r, t0 + pd.Timedelta(minutes=10))


def bar(o, h, low, c, v=10_000):
    return pd.Series({"open": o, "high": h, "low": low, "close": c, "volume": v})


T = lambda hhmm: pd.Timestamp(f"2026-03-02 {hhmm}", tz="America/New_York")  # noqa: E731


def test_stop_entry_fills_at_trigger_or_gap_open_and_stop_wins_ties():
    b = SimBroker(10_000, NOCOST)
    b.submit_entry(make_signal(), 10, T("09:55"))
    assert b.on_bar("AAA", T("09:55"), bar(100.5, 100.9, 100.4, 100.8)) == []          # not triggered
    ev = b.on_bar("AAA", T("10:00"), bar(101.2, 101.5, 101.1, 101.4))                 # gaps above trigger
    assert ev[0].kind == "filled" and b.positions["AAA"].raw_entry == pytest.approx(101.2)
    ev = b.on_bar("AAA", T("10:05"), bar(101.4, 104.0, 99.0, 102.0))                  # hits stop AND target
    assert ev[0].trade.exit_reason == "stop hit"


def test_entry_order_expires_and_volume_cap_partial_fill():
    b = SimBroker(10_000, NOCOST)
    b.submit_entry(make_signal(), 10, T("09:55"))
    b.on_bar("AAA", T("09:55"), bar(100.5, 100.6, 100.4, 100.5))
    b.on_bar("AAA", T("10:00"), bar(100.5, 100.6, 100.4, 100.5))
    ev = b.on_bar("AAA", T("10:05"), bar(100.5, 102.0, 100.4, 101.8))
    assert ev[0].kind == "expired" and not b.positions
    capped = SimBroker(10_000, CostConfig(reject_probability=0, max_fill_volume_fraction=0.01))
    capped.submit_entry(make_signal(), 50, T("09:55"))
    ev = capped.on_bar("AAA", T("09:55"), bar(101.0, 101.5, 100.9, 101.4, v=2_000))
    assert ev[0].kind == "partial" and capped.positions["AAA"].qty == 20


def test_costs_are_charged_and_reconcile_with_cash():
    costs = CostConfig(reject_probability=0, max_fill_volume_fraction=1.0)
    b = SimBroker(10_000, costs)
    b.submit_entry(make_signal(), 10, T("09:55"))
    b.on_bar("AAA", T("09:55"), bar(100.9, 101.2, 100.8, 101.1))
    b.on_bar("AAA", T("10:00"), bar(101.1, 103.2, 101.0, 103.0))      # target 103 + tick traded through
    t = b.trades[0]
    assert t.exit_reason == "target hit" and t.costs > 0 and t.net_pnl < t.gross_pnl
    assert b.cash == pytest.approx(10_000 + t.net_pnl)
