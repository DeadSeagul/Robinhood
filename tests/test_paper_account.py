"""Tests for the $10,000 options-only paper account (research/paper_account.py)."""
import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent / "research"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("paper_account", ROOT / "paper_account.py")
paper_account = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper_account)


def bars_file(path, start, rows):
    """Robinhood-style historicals JSON with 5-minute bars from start (UTC), rows of (open, high, low, close)."""
    times = pd.date_range(start, periods=len(rows), freq="5min", tz="UTC")
    bars = [dict(begins_at=f"{t:%Y-%m-%dT%H:%M:%SZ}", open_price=o, high_price=h, low_price=lo, close_price=c)
            for t, (o, h, lo, c) in zip(times, rows)]
    path.write_text(json.dumps({"data": {"results": [{"bars": bars}]}}))
    return str(path)


def test_option_size_and_fridays():
    assert paper_account.option_size(100, 0.20) == 5            # no float rounding down to 4
    assert paper_account.option_size(100, 0.99) == 1
    assert paper_account.option_size(100, 1.05) == 0
    assert paper_account.tradable("2026-11-05") and not paper_account.tradable("2026-11-06")


def test_a_trade_is_sized_from_the_balance_and_compounds(tmp_path, monkeypatch):
    orb = tmp_path / "orb.csv"
    pd.DataFrame([dict(date="2026-11-02", side="long", or_high=699.0, or_low=697.0, entry_time="09:35"),
                  dict(date="2026-11-03", side="long", or_high=699.0, or_low=697.0, entry_time="09:35")]).to_csv(orb, index=False)
    monkeypatch.setattr(paper_account, "ORB_LOG", orb)
    monkeypatch.setattr(paper_account, "OPT_LOG", tmp_path / "book.csv")
    qqq = bars_file(tmp_path / "qqq.json", "2026-11-02 14:30", [(700, 700.5, 699.5, 700)] * 20)
    opt = bars_file(tmp_path / "opt.json", "2026-11-02 14:35", [(0.49, 0.55, 0.45, 0.52), (0.52, 1.05, 0.50, 1.00)]
                    + [(1.0, 1.0, 1.0, 1.0)] * 18)
    paper_account.option(Namespace(date="2026-11-02", option_bars=opt, contract="11/3 705C", bars=qqq))
    book = paper_account.read_book()
    assert book.contracts.iat[0] == 2 and book.opt_reason.iat[0] == "target"   # $100 buys two at 0.50
    assert book.pnl.iat[0] == round(2 * ((1.00 - 0.50) * 100 - 0.09), 2)
    assert book.balance.iat[0] == round(10_000 + book.pnl.iat[0], 2)
    with pytest.raises(SystemExit):   # $101 can't buy a contract at 1.10
        dear = bars_file(tmp_path / "dear.json", "2026-11-03 14:35", [(1.09, 1.1, 1.0, 1.05)] * 20)
        paper_account.option(Namespace(date="2026-11-03", option_bars=dear, contract="11/4 700C", bars=qqq))
