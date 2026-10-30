"""Tests for the $10,000 paper account (research/paper_account.py)."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent / "research"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("paper_account", ROOT / "paper_account.py")
paper_account = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper_account)


def signals(dates, side="long", entry=700.0, exit_px=702.0):
    return pd.DataFrame(dict(date=dates, side=side, or_high=699.0, or_low=697.0, share_entry=entry,
                             share_exit=exit_px, share_reason="time", share_r=0.67))


def test_share_size_is_capped_by_risk_and_by_buying_power():
    assert paper_account.share_size(10_000, 700, 690) == 10    # $100 risk / $10 a share
    assert paper_account.share_size(10_000, 700, 697) == 28    # 33 by risk, but $20,000 buys only 28
    assert paper_account.option_size(100, 0.20) == 5            # no float rounding down to 4
    assert paper_account.option_size(100, 0.99) == 1
    assert paper_account.option_size(100, 1.05) == 0


def test_fridays_are_skipped_and_the_fourth_day_trade_in_five_days_is_blocked():
    book = paper_account.shares_book(signals(["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05",
                                              "2026-11-06", "2026-11-09"]), "2026-11-02")
    assert list(book.date) == ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-09"]
    assert list(book.shares > 0) == [True, True, True, False, True]   # 11/9's window (11/3-11/9) holds 2 trades
    first = book.iloc[0]
    assert first.shares == 28 and first.pnl == round(28 * (2.0 - 0.02), 2)


def test_short_pnl_and_compounding():
    book = paper_account.shares_book(signals(["2026-11-02", "2026-11-03"], side="short", entry=695.0,
                                             exit_px=699.0), "2026-11-02")
    assert book.shares.iat[0] == 25 and book.pnl.iat[0] == round(-25 * 4.02, 2)   # $4 risk a share, stopped
    assert book.balance.iat[1] == round(10_000 + book.pnl.sum(), 2)
    assert book.shares.iat[1] == 24                              # 1% of the smaller balance buys fewer shares
