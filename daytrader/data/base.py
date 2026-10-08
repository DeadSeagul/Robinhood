"""Market-data interfaces shared by every provider.

Intraday bars: DataFrame indexed by the bar's START time (tz-aware, America/New_York), columns
open/high/low/close/volume, regular trading hours only. Daily bars: indexed by session date.
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

import pandas as pd

NY = "America/New_York"
BAR_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataError(RuntimeError):
    pass


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    source: str

    @property
    def spread_pct(self) -> float:
        mid = (self.bid + self.ask) / 2
        return (self.ask - self.bid) / mid if mid > 0 else float("inf")


@dataclass(frozen=True)
class NewsItem:
    symbol: str
    headline: str
    created_at: datetime
    source: str
    url: str = ""


class DataProvider(Protocol):
    name: str

    def intraday_bars(self, symbol: str, start: date, end: date, minutes: int = 5) -> pd.DataFrame: ...

    def daily_bars(self, symbol: str, start: date, end: date) -> pd.DataFrame: ...


class QuoteProvider(Protocol):
    def latest_quote(self, symbol: str) -> Quote: ...


class NewsProvider(Protocol):
    def news(self, symbols: list[str], start: datetime, end: datetime) -> list[NewsItem]: ...


def regular_hours(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.between_time("09:30", "15:59")


def validate_bars(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Drop malformed rows and fail loudly on structural problems."""
    missing = [c for c in BAR_COLUMNS if c not in df.columns]
    if missing:
        raise DataError(f"{symbol}: missing columns {missing}")
    if df.index.tz is None:
        raise DataError(f"{symbol}: bar timestamps must be timezone-aware")
    df = df[BAR_COLUMNS].dropna()
    df = df[(df.high >= df.low) & (df.volume >= 0) & (df.low > 0)]
    df = df[~df.index.duplicated(keep="first")].sort_index()
    return df


def with_retries(fn, attempts: int = 4, base_delay: float = 1.0, retry_on: tuple = (Exception,)):
    """Call fn(); on failure retry with exponential backoff (1s, 2s, 4s ...)."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except retry_on as exc:  # noqa: PERF203
            last = exc
            if i < attempts - 1:
                _time.sleep(base_delay * 2 ** i)
    raise DataError(f"giving up after {attempts} attempts: {last}") from last
