"""Alpaca Market Data API (documented, supported).

Keys come from the environment: APCA_API_KEY_ID and APCA_API_SECRET_KEY.
- Free plan: real-time data is IEX only; full-market SIP bars are available once they are more
  than 15 minutes old, so backtests use feed="sip" and live polling uses feed="iex".
- News comes from Benzinga via /v1beta1/news, with history back to 2015.
Docs: https://docs.alpaca.markets/docs/about-market-data-api
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from .base import NY, DataError, NewsItem, Quote, regular_hours, validate_bars, with_retries

DATA_URL = "https://data.alpaca.markets"


def alpaca_headers() -> dict[str, str]:
    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise DataError("Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in the environment (never in code).")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


class AlpacaDataProvider:
    name = "alpaca market data"

    def __init__(self, feed: str = "sip", session: requests.Session | None = None):
        self.feed = feed
        self.session = session or requests.Session()

    def _get(self, path: str, params: dict) -> dict:
        def call():
            r = self.session.get(DATA_URL + path, params=params, headers=alpaca_headers(), timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"retryable {r.status_code}")
            if r.status_code >= 400:
                raise DataError(f"Alpaca {r.status_code}: {r.text[:200]}")
            return r.json()

        return with_retries(call, retry_on=(requests.RequestException,))

    def _bars(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        rows, token = [], None
        while True:
            params = {"timeframe": timeframe, "start": start.isoformat(), "end": end.isoformat(),
                      "feed": self.feed, "adjustment": "split", "limit": 10000}
            if token:
                params["page_token"] = token
            payload = self._get(f"/v2/stocks/{symbol}/bars", params)
            rows += payload.get("bars") or []
            token = payload.get("next_page_token")
            if not token:
                break
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(rows).rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        df.index = pd.to_datetime(df.pop("t"), utc=True).dt.tz_convert(NY)
        return validate_bars(df, symbol)

    def intraday_bars(self, symbol: str, start: date | None = None, end: date | None = None,
                      minutes: int = 5) -> pd.DataFrame:
        end = end or date.today()
        start = start or end - timedelta(days=365)
        s = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        e = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)
        e = min(e, datetime.now(timezone.utc) - timedelta(minutes=16))  # SIP needs data > 15 min old
        return regular_hours(self._bars(symbol, f"{minutes}Min", s, e))

    def daily_bars(self, symbol: str, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        end = end or date.today()
        start = start or end - timedelta(days=730)
        s = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        e = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)
        e = min(e, datetime.now(timezone.utc) - timedelta(minutes=16))
        df = self._bars(symbol, "1Day", s, e)
        df.index = pd.DatetimeIndex(df.index.date)
        return df

    def latest_quote(self, symbol: str) -> Quote:
        q = self._get(f"/v2/stocks/{symbol}/quotes/latest", {"feed": "iex"})["quote"]
        return Quote(symbol, float(q["bp"]), float(q["ap"]), pd.Timestamp(q["t"]).to_pydatetime(),
                     "alpaca/iex")

    def news(self, symbols: list[str], start: datetime, end: datetime) -> list[NewsItem]:
        items, token = [], None
        while True:
            params = {"symbols": ",".join(symbols), "start": start.isoformat(), "end": end.isoformat(),
                      "limit": 50, "sort": "desc"}
            if token:
                params["page_token"] = token
            payload = self._get("/v1beta1/news", params)
            for n in payload.get("news", []):
                for sym in n.get("symbols", []):
                    if sym in symbols:
                        items.append(NewsItem(sym, n.get("headline", ""), pd.Timestamp(n["created_at"]).to_pydatetime(),
                                              n.get("source", "benzinga"), n.get("url", "")))
            token = payload.get("next_page_token")
            if not token:
                break
        return items
