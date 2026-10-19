"""Add Robinhood 5-minute bars to the chart-replay archive without printing a single price.

Yahoo only serves the last ~60 sessions of 5-minute bars, and every one of those dates is now used or was watched
live, so the drills in replay.py need older days. Robinhood's get_equity_historicals has them. Claude Code saves a
large tool result straight to a file (a "saved to: .../tool-results/..." line), so the bars can reach disk without
passing through anyone's context. This script merges such files into data_cache/archive/{SYMBOL}_5m.json, in the
same Yahoo chart format replay.py reads. It prints only symbols, dates and counts, so running it can't spoil a drill.

  python3 -I research/archive_add.py FILE [FILE ...] [--delete]    # --delete removes each input once merged
  python3 -I research/archive_add.py --summary                     # what the archive holds (dates only)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ARCHIVE = Path(__file__).resolve().parent.parent / "data_cache" / "archive"
COLS = ["open", "high", "low", "close", "volume"]


def load_result(path: Path) -> dict:
    """The tool's JSON, whether saved raw or wrapped (a list of {"type": "text", "text": ...} blocks, or a preamble)."""
    text = path.read_text()
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        doc = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if isinstance(doc, list):
        doc = next(json.loads(b["text"]) for b in doc if isinstance(b, dict) and "data" in b.get("text", ""))
    return doc


def parse(path: Path) -> dict[str, pd.DataFrame]:
    """Robinhood get_equity_historicals JSON -> {symbol: bars indexed by UTC start time}."""
    out = {}
    for res in load_result(path)["data"]["results"]:
        raw = res.get("bars") or []
        bars = [b for b in raw if not b.get("interpolated") and b.get("session", "reg") == "reg"]
        if len(bars) < len(raw):
            print(f"{path.name}: {res.get('symbol')}: dropped {len(raw) - len(bars)} of {len(raw)} bars "
                  f"(sessions {sorted({str(b.get('session')) for b in raw})})")
        if not bars:
            continue
        df = pd.DataFrame({"open": [float(b["open_price"]) for b in bars], "high": [float(b["high_price"]) for b in bars],
                           "low": [float(b["low_price"]) for b in bars], "close": [float(b["close_price"]) for b in bars],
                           "volume": [int(b.get("volume") or 0) for b in bars]},
                          index=pd.to_datetime([b["begins_at"] for b in bars], utc=True))
        out[res["symbol"].upper()] = df
    return out


def read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], tz="UTC"))
    r = json.loads(path.read_text())["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    return pd.DataFrame({k: q[k] for k in COLS}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True))


def write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    quote = {k: [float(x) for x in df[k]] for k in COLS[:4]} | {"volume": [int(x) for x in df.volume]}
    chart = {"chart": {"result": [{"meta": {"source": "robinhood get_equity_historicals 5minute regular"},
                                   "timestamp": [int(t.timestamp()) for t in df.index],
                                   "indicators": {"quote": [quote]}}]}}
    path.write_text(json.dumps(chart))


def describe(sym: str, df: pd.DataFrame) -> str:
    ny = df.index.tz_convert("America/New_York")
    per_day = pd.Series(1, index=ny).groupby(ny.date).size()
    full = per_day[per_day >= 70]
    if full.empty:
        return f"{sym}: no full sessions"
    return f"{sym}: {len(full)} full sessions, {full.index[0]} to {full.index[-1]}"


def merge(paths: list[Path], delete: bool = False, archive: Path = ARCHIVE) -> int:
    """Merge each file into the archive; returns how many files added nothing (those are never deleted)."""
    empty = 0
    for p in paths:
        parsed = parse(p)
        for sym, new in parsed.items():
            dest = archive / f"{sym}_5m.json"
            old = read(dest)
            df = pd.concat([old, new])
            df = df[~df.index.duplicated(keep="last")].sort_index()
            write(dest, df)
            print(f"{p.name}: +{len(df) - len(old)} bars -> {describe(sym, df)}")
        if not parsed:
            empty += 1
            print(f"{p.name}: NO BARS FOUND - kept the file for inspection")
        elif delete:
            p.unlink()
    return empty


def summary(archive: Path = ARCHIVE) -> None:
    files = sorted(archive.glob("*_5m.json"))
    if not files:
        print(f"Archive is empty ({archive}).")
    for f in files:
        print(describe(f.name.split("_")[0], read(f)))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("files", nargs="*", type=Path)
    p.add_argument("--delete", action="store_true")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args(argv)
    empty = merge(args.files, args.delete) if args.files else 0
    if args.summary or not args.files:
        summary()
    if empty:
        raise SystemExit(f"{empty} file(s) had no bars.")


if __name__ == "__main__":
    main()
