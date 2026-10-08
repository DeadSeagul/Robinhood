"""Alpaca PAPER trading adapter (documented REST API, https://docs.alpaca.markets).

Hard-wired to the paper endpoint; there is deliberately no way to point it at a live account.
Entries go out as day bracket orders (buy-stop entry + take-profit + stop-loss) so the protective
stop lives at the broker. Without a target it uses a one-triggers-other order with only a stop.
The adapter keeps a local book of working orders and positions, synced from Alpaca on every bar,
so the shared DaySession logic works unchanged.
"""
from __future__ import annotations

import os

import pandas as pd
import requests

from ..data.base import DataError, with_retries
from ..strategy import EntrySignal
from .base import BrokerEvent, Position, Trade, WorkingOrder

PAPER_URL = "https://paper-api.alpaca.markets"


class AlpacaPaperBroker:
    def __init__(self, session: requests.Session | None = None, base_url: str = PAPER_URL):
        if base_url != PAPER_URL:
            raise PermissionError("AlpacaPaperBroker only talks to the paper endpoint.")
        self.base_url = base_url
        self.session = session or requests.Session()
        self.working: dict[str, WorkingOrder] = {}
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.log: list[BrokerEvent] = []

    # --- HTTP ---------------------------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
        if not key or not secret:
            raise DataError("Set APCA_API_KEY_ID and APCA_API_SECRET_KEY (paper keys) in the environment.")
        return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

    def _req(self, method: str, path: str, **kw):
        def call():
            r = self.session.request(method, self.base_url + path, headers=self._headers(), timeout=20, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"retryable {r.status_code}")
            return r

        r = with_retries(call, retry_on=(requests.RequestException,))
        if r.status_code >= 400:
            raise DataError(f"Alpaca {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.content else {}

    @staticmethod
    def entry_payload(signal: EntrySignal, qty: int) -> dict:
        body = {"symbol": signal.symbol, "qty": str(qty), "side": "buy", "time_in_force": "day",
                "client_order_id": f"orb-{signal.symbol}-{signal.created_at.strftime('%Y%m%d%H%M')}"}
        if signal.order_type == "stop":
            body.update(type="stop", stop_price=f"{signal.trigger:.2f}")
        else:
            body.update(type="market")
        target = signal.target(signal.trigger)
        if target is not None:
            body.update(order_class="bracket", take_profit={"limit_price": f"{target:.2f}"},
                        stop_loss={"stop_price": f"{signal.stop_loss:.2f}"})
        else:
            body.update(order_class="oto", stop_loss={"stop_price": f"{signal.stop_loss:.2f}"})
        return body

    # --- account ------------------------------------------------------------------------------
    @property
    def cash(self) -> float:
        return float(self._req("GET", "/v2/account")["cash"])

    def equity(self, prices: dict[str, float] | None = None) -> float:
        return float(self._req("GET", "/v2/account")["equity"])

    def available_cash(self) -> float:
        reserved = sum(w.qty * w.signal.trigger * 1.001 for w in self.working.values())
        return self.cash - reserved

    # --- orders -------------------------------------------------------------------------------
    def submit_entry(self, signal: EntrySignal, qty: int, at: pd.Timestamp) -> BrokerEvent | None:
        try:
            order = self._req("POST", "/v2/orders", json=self.entry_payload(signal, qty))
        except DataError as exc:
            return self._event("rejected", signal.symbol, at, str(exc))
        self.working[signal.symbol] = WorkingOrder(signal, qty, at, order.get("id", ""))
        return None

    def cancel_entries(self, at: pd.Timestamp, reason: str) -> list[BrokerEvent]:
        out = []
        for sym, w in list(self.working.items()):
            try:
                self._req("DELETE", f"/v2/orders/{w.order_id}")
            except DataError as exc:  # already filled or gone; the next sync will tell
                self.log.append(BrokerEvent("warning", sym, at, str(exc)))
                continue
            del self.working[sym]
            out.append(self._event("expired", sym, at, reason))
        return out

    def flatten_all(self, at: pd.Timestamp, prices: dict[str, float] | None, reason: str) -> list[BrokerEvent]:
        self._req("DELETE", "/v2/orders")
        self._req("DELETE", "/v2/positions")
        out = []
        for sym, p in list(self.positions.items()):
            px = (prices or {}).get(sym) or p.raw_entry
            out.append(self._close(sym, at, px, f"{reason} (approximate price; check fills)"))
        self.working.clear()
        return out

    def on_bar(self, symbol: str, ts: pd.Timestamp, bar: pd.Series) -> list[BrokerEvent]:
        """Sync this symbol's order and position state from Alpaca."""
        out = []
        w = self.working.get(symbol)
        if w is not None:
            o = self._req("GET", f"/v2/orders/{w.order_id}", params={"nested": "true"})
            status = o.get("status")
            if status in ("filled", "partially_filled") and float(o.get("filled_qty") or 0) > 0:
                del self.working[symbol]
                raw = float(o["filled_avg_price"])
                legs = {leg.get("type"): leg for leg in o.get("legs") or []}
                self.positions[symbol] = Position(symbol, int(float(o["filled_qty"])), raw, raw, w.signal.stop_loss,
                                                  w.signal.target(w.signal.trigger), ts, w.signal, 0.0, legs)
                out.append(self._event("filled" if status == "filled" else "partial", symbol, ts,
                                       f"bought {o['filled_qty']} @ {raw:.2f}"))
            elif status in ("canceled", "expired", "rejected"):
                del self.working[symbol]
                out.append(self._event("rejected" if status == "rejected" else "expired", symbol, ts, status))
            elif ts >= w.signal.expires_at:
                out += self.cancel_entries(ts, "entry not triggered in time")
        p = self.positions.get(symbol)
        if p is not None and p.entry_time != ts:
            for leg in p.legs.values():
                lo = self._req("GET", f"/v2/orders/{leg['id']}")
                if lo.get("status") == "filled":
                    why = "target hit" if lo.get("type") == "limit" else "stop hit"
                    out.append(self._close(symbol, ts, float(lo["filled_avg_price"]), why))
                    break
        return out

    def _close(self, symbol: str, ts, px: float, reason: str) -> BrokerEvent:
        p = self.positions.pop(symbol)
        pnl = p.qty * (px - p.raw_entry)
        t = Trade(symbol, p.qty, p.entry_time, ts, p.raw_entry, p.entry_price, px, px, p.stop, p.target, reason,
                  pnl, 0.0, pnl, p.qty * (p.raw_entry - p.stop), list(p.signal.reasons))
        self.trades.append(t)
        return self._event("exit", symbol, ts, reason, t)

    def _event(self, kind, symbol, at, detail="", trade=None) -> BrokerEvent:
        ev = BrokerEvent(kind, symbol, at, detail, trade)
        self.log.append(ev)
        return ev
