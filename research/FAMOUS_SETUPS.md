# Famous traders' setups, backtested

On 2026-10-14 the user asked me to study the strategies of big-name traders such as TJR. The research write-up is in [`reports/Famous trader strategies compared.md`](../reports/Famous%20trader%20strategies%20compared.md), with sources in `research_notes/`. This file is the follow-up. I took the setups whose rules are mechanical enough to code and tested them on our own data with [`famous_setups.py`](famous_setups.py).

**Method.** All rules were fixed before the first run, with no parameter tuning. The exact rules are in the script's docstring.

| | Detail |
|---|---|
| Intraday data | 5-minute bars, regular hours, 2026-07-22 → 2026-10-13 (58 sessions) |
| Daily data | Daily bars, 2024-10-14 → 2026-10-13 |
| Symbols | The same fixed 63-symbol universe as the paper-trading system |
| Fills | Pessimistic: if one bar hits both the stop and the target, the stop counts |
| Costs | 1 bp per side intraday, 2 bp per side daily |

R is the amount risked per trade. |t| < 2 means the result is indistinguishable from luck.

| Setup (whose) | Bars | Trades | Win rate | Avg R after costs | Avg R before costs | t | First half / second half |
|---|---|---|---|---|---|---|---|
| Liquidity sweep → structure shift → fair-value-gap entry, 2R target (ICT, the model TJR teaches) | 5-min | 23 | 48% | +0.23 | +0.26 | 0.9 | −0.24 / +0.66 |
| Same, target = the opposite prior-day level | 5-min | 23 | 48% | +0.28 | +0.31 | 1.0 | −0.22 / +0.74 |
| Silver Bullet, 10:00–11:00 fair value gap (ICT) | 5-min | 1,957 | 41% | **−0.08** | −0.03 | **−3.0** | −0.07 / −0.09 |
| Turtle Soup, real intraday buy-stop fill (Raschke) | 5-min + daily | 206 | 35% | −0.01 | +0.06 | −0.1 | −0.26 / +0.25 |
| Turtle Soup, entry at the reclaim close (Raschke) | daily | 916 | 33% | −0.14 | −0.10 | −1.8 | −0.14 / −0.14 |
| Holy Grail, ADX > 30 pullback to 20 EMA (Raschke) | daily | 225 | 40% | −0.04 | −0.03 | −0.4 | −0.06 / −0.03 |
| Momentum breakout with 10-day MA trail (Qullamaggie) | daily | 117 | 45% | −0.01 | 0.00 | −0.1 | −0.13 / +0.11 |

On QQQ and SPY alone, the sweep model fired once (−1.1R). The Silver Bullet fired 39 times (−0.03R).

## What this says

- **Nothing here shows an edge.** Every t-stat is under 2. The only significant result is negative: the mechanical Silver Bullet loses about 0.08R a trade after costs, over almost 2,000 trades.
- **Costs decide the intraday setups.** These setups use tight stops, so even 2 bp of round-trip cost is a large share of 1R. The Silver Bullet goes from −0.03R before costs to −0.08R after. For a small account buying options with spreads of 5–10% of the premium, the cost per trade is far larger than in this test.
- **The sweep-and-shift model is the only positive number, but it's too thin to read.** It needs a fresh sweep of yesterday's high or low in a session that opened inside yesterday's range, then a structure shift within 30 minutes, then a fair value gap that gets retested. That happened only 23 times in 58 sessions across 63 symbols, and only once on QQQ or SPY. The first half of the sample lost and the second half won. It's worth watching, not trading. That fits the independent tests in the research notes, which found no edge in ICT rules as taught.
- **The famous swing setups (Holy Grail, Qullamaggie breakouts) were flat on this universe.** Caveats:
  - 63 large, liquid stocks over two years.
  - Today's list of stocks, so delisted names are missing (survivorship bias).
  - Qullamaggie's real edge is claimed to come from the top 1–2% of all stocks by momentum, often small and mid caps. This universe can't test that.
- **One mistake to learn from.** A first version of Turtle Soup bought at the old low only on days that later *closed* above it. That uses the close to choose trades. It showed an impossible +1.2R per trade (t = 7.9), so I dropped it. When a backtest of a famous setup looks spectacular, look-ahead bias is the first thing to check.

## What this means for our trading

- **No live rule changes.** None of these setups passes the screen the paper-trading system uses (100+ trades, profit factor above 1.2, t ≥ 2).
- **Sweep-and-shift goes into practice drills, not live trading.** I'll tag it `liquidity-sweep-mss` in the chart-replay drills ([`REPLAY.md`](REPLAY.md)) and keep scoring it. The 5-minute data rolls forward each day, so its sample grows.
