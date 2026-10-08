"""Local CSV bars, e.g. converted Polygon/Massive or Databento flat files.

Expected files: <root>/<SYMBOL>_<minutes>m.csv and <root>/<SYMBOL>_1d.csv with columns
timestamp,open,high,low,close,volume. Intraday timestamps are bar starts in UTC or with an offset.
Flat files that include delisted symbols are the way to remove survivorship bias.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .base import NY, DataError, regular_hours, validate_bars
from .yahoo import _clip


class CSVProvider:
    name = "local csv"

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _read(self, path: Path, symbol: str) -> pd.DataFrame:
        if not path.exists():
            raise DataError(f"{symbol}: no file {path}")
        df = pd.read_csv(path)
        df.index = pd.to_datetime(df.pop("timestamp"), utc=True).dt.tz_convert(NY)
        return validate_bars(df, symbol)

    def intraday_bars(self, symbol: str, start: date | None = None, end: date | None = None,
                      minutes: int = 5) -> pd.DataFrame:
        return _clip(regular_hours(self._read(self.root / f"{symbol}_{minutes}m.csv", symbol)), start, end)

    def daily_bars(self, symbol: str, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        df = self._read(self.root / f"{symbol}_1d.csv", symbol)
        df.index = pd.DatetimeIndex(df.index.date)
        return _clip(df, start, end)
