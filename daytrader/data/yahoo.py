"""Yahoo Finance chart endpoint. RESEARCH USE ONLY.

The endpoint is unofficial and undocumented. It returns at most ~60 days of 5-minute bars and
only for symbols that still trade (survivorship bias). Use Alpaca or flat files for real work.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .base import NY, DataError, regular_hours, validate_bars, with_retries

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def parse_chart(payload: dict, symbol: str) -> tuple[pd.DataFrame, list[pd.Timestamp]]:
    try:
        res = payload["chart"]["result"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise DataError(f"{symbol}: unexpected Yahoo payload") from exc
    if not res.get("timestamp"):
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]), []
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(NY)
    df = pd.DataFrame({k: q[k] for k in ["open", "high", "low", "close", "volume"]}, index=idx)
    splits = [pd.Timestamp(int(v["date"]), unit="s", tz="UTC").tz_convert(NY)
              for v in (res.get("events", {}) or {}).get("splits", {}).values()]
    return df, splits


class YahooProvider:
    name = "yahoo (unofficial, research only)"

    def __init__(self, cache_dir: str | Path | None = None, session: requests.Session | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.session = session or requests.Session()
        self.splits: dict[str, list[pd.Timestamp]] = {}

    def _get(self, symbol: str, interval: str, rng: str) -> dict:
        cache = self.cache_dir / f"{symbol}_{interval}.json" if self.cache_dir else None
        if cache and cache.exists():
            return json.loads(cache.read_text())

        def call():
            r = self.session.get(URL.format(symbol=symbol),
                                 params={"interval": interval, "range": rng, "events": "split"},
                                 headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status()
            return r.json()

        payload = with_retries(call)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(payload))
        return payload

    def intraday_bars(self, symbol: str, start: date | None = None, end: date | None = None,
                      minutes: int = 5) -> pd.DataFrame:
        df, splits = parse_chart(self._get(symbol, f"{minutes}m", "60d"), symbol)
        self.splits[symbol] = splits
        df = regular_hours(validate_bars(df, symbol))
        return _clip(df, start, end)

    def daily_bars(self, symbol: str, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        df, _ = parse_chart(self._get(symbol, "1d", "2y"), symbol)
        df = validate_bars(df, symbol)
        df.index = pd.DatetimeIndex(df.index.date)
        return _clip(df, start, end)


def _clip(df: pd.DataFrame, start, end) -> pd.DataFrame:
    if df.empty:
        return df
    dates = pd.Series(df.index.date, index=df.index)
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dates >= start
    if end is not None:
        mask &= dates <= end
    return df[mask.values]
