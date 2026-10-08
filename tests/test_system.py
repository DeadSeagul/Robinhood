from datetime import timedelta

import pandas as pd
import pytest
import requests

from daytrader.analytics import go_no_go, metrics
from daytrader.backtest import run_backtest
from daytrader.broker.alpaca_paper import PAPER_URL, AlpacaPaperBroker
from daytrader.broker.sim import SimBroker
from daytrader.config import AppConfig, ScannerConfig, StrategyConfig
from daytrader.live import PaperTrader
from daytrader.strategy import EntrySignal

CFG = AppConfig(mode="backtest", scanner=ScannerConfig(lookback_days=20))


def test_backtest_finds_the_planted_breakout(synthetic_market):
    intraday, daily, days = synthetic_market
    res = run_backtest(intraday, daily, CFG, StrategyConfig(), "V1")
    assert [t.symbol for t in res.trades] == ["AAA"]
    t = res.trades[0]
    assert t.entry_time.date() == days[-1] and t.entry_time.time() >= pd.Timestamp("09:55").time()
    assert res.violations == []
    assert res.daily_equity.iloc[-1] == pytest.approx(CFG.risk.starting_equity + t.net_pnl)


def test_no_lookahead_future_changes_do_not_alter_past_decisions(synthetic_market):
    intraday, daily, days = synthetic_market
    base = run_backtest(intraday, daily, CFG, StrategyConfig(), "V1")
    cut = pd.Timestamp(days[-1]).tz_localize("America/New_York") + pd.Timedelta(hours=10, minutes=0)
    changed = {s: b.copy() for s, b in intraday.items()}
    a = changed["AAA"]
    a.loc[a.index >= cut, ["open", "high", "low", "close"]] = 50.0   # crash after 10:00
    alt = run_backtest(changed, daily, CFG, StrategyConfig(), "V1")
    before = lambda r: [(p.ticker, p.timestamp, p.entry_trigger, p.stop_loss) for p in r.proposals if p.timestamp <= cut]  # noqa: E731
    assert before(base) == before(alt)
    assert base.trades[0].entry_time == alt.trades[0].entry_time      # same entry; only the exit differs


def test_metrics_and_screen_reject_small_samples(synthetic_market):
    intraday, daily, _ = synthetic_market
    res = run_backtest(intraday, daily, CFG, StrategyConfig(), "V1")
    m = metrics(res.trades, res.daily_equity, res.start_equity)
    ok, fails = go_no_go(m)
    assert not ok and any("trades" in f for f in fails)


# --- Alpaca paper adapter -----------------------------------------------------------------------
class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._p = status, payload or {}
        self.content = b"x"
        self.text = str(self._p)

    def json(self):
        return self._p


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return self.responses.pop(0)


def sig():
    t0 = pd.Timestamp("2026-03-02 09:55", tz="America/New_York")
    return EntrySignal("AAA", t0, "stop", 101.0, 100.0, 2.0, t0 + pd.Timedelta(minutes=10))


def test_alpaca_adapter_is_paper_only_and_builds_bracket(monkeypatch):
    with pytest.raises(PermissionError):
        AlpacaPaperBroker(base_url="https://api.alpaca.markets")
    p = AlpacaPaperBroker.entry_payload(sig(), 10)
    assert p["order_class"] == "bracket" and p["type"] == "stop" and p["stop_price"] == "101.00"
    assert p["take_profit"] == {"limit_price": "103.00"} and p["stop_loss"] == {"stop_price": "100.00"}
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    fs = FakeSession([FakeResp(200, {"id": "o1"}),
                      FakeResp(200, {"status": "filled", "filled_qty": "10", "filled_avg_price": "101.02",
                                     "legs": [{"id": "tp", "type": "limit"}, {"id": "sl", "type": "stop"}]}),
                      FakeResp(200, {"status": "new", "type": "limit"}),
                      FakeResp(200, {"status": "filled", "type": "stop", "filled_avg_price": "99.98"})])
    b = AlpacaPaperBroker(session=fs)
    assert b.submit_entry(sig(), 10, sig().created_at) is None
    assert fs.calls[0][1] == PAPER_URL + "/v2/orders"
    t1 = sig().created_at + timedelta(minutes=5)
    evs = b.on_bar("AAA", t1, pd.Series({"open": 1.0}))
    assert evs[0].kind == "filled" and "AAA" in b.positions
    evs = b.on_bar("AAA", t1 + timedelta(minutes=5), pd.Series({"open": 1.0}))
    assert evs[-1].kind == "exit" and b.trades[0].raw_exit == pytest.approx(99.98)


def test_alpaca_adapter_requires_env_keys(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    with pytest.raises(Exception, match="APCA_API_KEY_ID"):
        AlpacaPaperBroker(session=FakeSession([])).equity()


# --- paper trader end to end ------------------------------------------------------------------
class ReplayProvider:
    """Serves historical bars as if live: only bars that have completed before the fake clock."""
    name = "replay"

    def __init__(self, intraday, daily, clock):
        self.intraday, self.daily, self.clock = intraday, daily, clock

    def intraday_bars(self, symbol, start, end, minutes=5):
        b = self.intraday[symbol]
        now = pd.Timestamp(self.clock())
        b = b[(b.index + pd.Timedelta(minutes=5)) <= now]
        dates = pd.Series(b.index.date, index=b.index)
        return b[((dates >= start) & (dates <= end)).values]

    def daily_bars(self, symbol, start, end):
        d = self.daily[symbol]
        return d[(d.index.date >= start) & (d.index.date <= end)]


def make_trader(synthetic_market, tmp_path, kill_at=None):
    intraday, daily, days = synthetic_market
    state = {"now": pd.Timestamp(days[-1]).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=10)}
    kill = tmp_path / "KILL_SWITCH"

    def sleep(sec):
        state["now"] += pd.Timedelta(seconds=sec)
        if kill_at is not None and state["now"] >= kill_at:
            kill.write_text("stop")

    cfg = AppConfig(mode="paper", scanner=ScannerConfig(lookback_days=20), kill_switch_path=str(kill))
    prov = ReplayProvider(intraday, daily, lambda: state["now"])
    broker = SimBroker(cfg.risk.starting_equity, cfg.costs)
    return PaperTrader(cfg, prov, broker, ["AAA", "SPY", "QQQ"], clock=lambda: state["now"], sleep=sleep), broker


def test_paper_trader_replays_a_day_and_matches_backtest(synthetic_market, tmp_path):
    trader, broker = make_trader(synthetic_market, tmp_path)
    rep = trader.run_day(tmp_path / "journal")
    assert [t.symbol for t in rep.trades] == ["AAA"] and not rep.violations
    assert (tmp_path / "journal").exists()
    bt = run_backtest(*synthetic_market[:2], CFG, StrategyConfig(), "V1")
    assert rep.trades[0].entry_time == bt.trades[0].entry_time


def test_kill_switch_flattens_and_stops(synthetic_market, tmp_path):
    days = synthetic_market[2]
    kill_at = pd.Timestamp(days[-1]).tz_localize("America/New_York") + pd.Timedelta(hours=10, minutes=3)   # after the 9:55 fill, before the target
    trader, broker = make_trader(synthetic_market, tmp_path, kill_at)
    rep = trader.run_day()
    assert not broker.positions and not broker.working
    assert any("kill switch" in e for e in rep.risk_events)
    assert rep.trades and rep.trades[0].exit_reason == "kill switch activated"


def test_network_errors_trigger_reconnect_then_halt(synthetic_market, tmp_path):
    trader, broker = make_trader(synthetic_market, tmp_path)
    real = trader.provider.intraday_bars
    calls = {"n": 0}

    def flaky(symbol, start, end, minutes=5):
        if start == end and pd.Timestamp(trader.clock()).time() >= pd.Timestamp("10:20").time():
            calls["n"] += 1
            raise requests.ConnectionError("feed down")
        return real(symbol, start, end, minutes)

    trader.provider.intraday_bars = flaky
    rep = trader.run_day()
    assert any("critical system error" in e for e in rep.risk_events)
    assert not broker.positions
