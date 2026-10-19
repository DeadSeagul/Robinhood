"""Tests for the Robinhood replay archive (research/archive_add.py) and how replay.py merges it with Yahoo data."""
import importlib.util
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent / "research"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


archive_add, replay = load("archive_add"), load("replay")


def rh_file(tmp_path, name, day, price, symbol="QQQ", extra=()):
    """A Robinhood historicals result for one full session (13:30-19:55 UTC) at a flat price."""
    times = pd.date_range(f"{day} 13:30", f"{day} 19:55", freq="5min", tz="UTC")
    bars = [{"begins_at": f"{t:%Y-%m-%dT%H:%M:%SZ}", "open_price": str(price), "high_price": str(price + 1),
             "low_price": str(price - 1), "close_price": str(price), "volume": 100, "session": "reg"} for t in times]
    bars += list(extra)
    path = tmp_path / name
    path.write_text(json.dumps({"data": {"results": [{"symbol": symbol, "bars": bars}]}, "guide": ""}))
    return path


def yahoo_file(directory, day, price, symbol="QQQ"):
    times = pd.date_range(f"{day} 13:30", f"{day} 19:55", freq="5min", tz="UTC")
    n = len(times)
    quote = {"open": [price] * n, "high": [price + 1] * n, "low": [price - 1] * n, "close": [price] * n,
             "volume": [100] * n}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{symbol}_5m.json").write_text(json.dumps({"chart": {"result": [
        {"timestamp": [int(t.timestamp()) for t in times], "indicators": {"quote": [quote]}}]}}))


def test_merge_round_trips_and_dedupes(tmp_path):
    arc = tmp_path / "archive"
    ghost = {"begins_at": "2026-03-10T20:00:00Z", "open_price": "1", "high_price": "1", "low_price": "1",
             "close_price": "1", "volume": 0, "interpolated": True}
    a = rh_file(tmp_path, "a.txt", "2026-03-10", 600.0, extra=[ghost])
    b = rh_file(tmp_path, "b.txt", "2026-03-10", 601.0)  # same session again: later file wins, no duplicates
    archive_add.merge([a, b], archive=arc)
    df = archive_add.read(arc / "QQQ_5m.json")
    assert len(df) == 78 and df.close.eq(601.0).all()
    days = replay.load_sessions("QQQ", data=tmp_path / "none", archive=arc)
    assert list(days) == [pd.Timestamp("2026-03-10").date()] and len(days[pd.Timestamp("2026-03-10").date()]) == 78


def test_delete_removes_inputs_only_after_merging(tmp_path):
    a = rh_file(tmp_path, "a.txt", "2026-03-10", 600.0)
    archive_add.merge([a], delete=True, archive=tmp_path / "archive")
    assert not a.exists() and (tmp_path / "archive" / "QQQ_5m.json").exists()


def test_archive_wins_over_yahoo_and_both_sources_combine(tmp_path):
    yahoo, arc = tmp_path / "yahoo", tmp_path / "archive"
    yahoo_file(yahoo, "2026-03-11", 500.0)
    archive_add.merge([rh_file(tmp_path, "a.txt", "2026-03-10", 600.0),
                       rh_file(tmp_path, "b.txt", "2026-03-11", 700.0)], archive=arc)
    days = replay.load_sessions("QQQ", data=yahoo, archive=arc)
    assert [str(d) for d in days] == ["2026-03-10", "2026-03-11"]
    assert days[pd.Timestamp("2026-03-11").date()].close.eq(700.0).all()
