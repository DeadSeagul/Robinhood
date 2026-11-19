# Part 4: which other stock could we day trade? Fixed before running

Written 2026-11-19 before any data for these symbols was downloaded. The user asked: "what other stock could we day trade?"
The user's rules still hold: no searching across settings, every test reported, and screening results only.

## The list, chosen by a rule that was already written down

These are the 8 biggest QQQ holdings named in the morning news routine (`SCHEDULED_TASKS.md`), plus the two other most-traded index ETFs:
- NVDA, MSFT, AAPL, AMZN, META, GOOGL, AVGO, TSLA;
- SPY and IWM.

QQQ's results from part 3 are shown alongside for comparison, not re-tested.

**Survivorship bias:** these are today's giants, so the list already knows which companies won the last decade. Both rules
trade long and short, which limits that bias, but doesn't remove it.

**Options fit (Robinhood, checked 2026-11-19):**
- SPY and IWM have daily expirations.
- NVDA, TSLA and AAPL list Monday/Wednesday/Friday expirations, with a 5-cent tick above $3.
- So the next-day option rule only fits SPY and IWM every day.

## Data

- Alpaca 5-minute SIP bars, 2016-01-04 → 2026-11-18, regular hours, `adjustment=raw`. Raw prices are the real traded
  prices; intraday trades never span a split.
- META's history before its 2022 rename (FB) comes through Alpaca's symbol mapping. If a symbol's history doesn't reach back to 2016, the gap is reported.
- Sessions without a 9:30 bar or with fewer than 40 bars are dropped, as before.

## Rules (the same code as part 3)

- **R1, our 5-min ORB:** `paper_orb.signal` + `share_trade`. Entry after the first 5-minute close beyond the 9:30 bar's range (by 11:25), stop at the other side, 2R target, 90-minute exit.
- **R2, first-candle ORB:** Zarattini & Aziz. Trade the 9:30 candle's direction, entry at 9:35, stop at that candle's low/high, 10R target or the close.
- **R3, "stock in play" (one trade a day across the 8 stocks):**
  - **Pick:** each day at 9:35, the stock whose 9:30 bar volume, divided by its average 9:30 bar volume over the previous 14 sessions, is highest.
  - **Rules:** trade it with R1 (R3a) and with R2 (R3b). Days on which the picked stock has no R1 signal have no R3a trade.
  - **Source:** the idea comes from Zarattini, Barbon & Aziz's follow-up paper, simplified to this fixed list.
- **Costs:** $0.01 per share on each side, at the real price. That's a full tick each way, conservative for these names. Results are shown before and after costs.

## Measures and the bar

- **Per trade:** return, trade count, win rate, mean with its t, and halves 2016-01 → 2021-06 and 2021-07 → 2026-11.
- **Number of tests:** 22 (10 symbols × 2 rules, plus R3a and R3b).
- **Bar:** a symbol and rule count as worth day trading only if **t ≥ 3.1 after costs** (the 5% level corrected for 22 tests) and the mean is positive in **both halves**.
- **Ranking:** all 22 are ranked by t after costs. If none passes, the answer is that none of these showed an edge that beats luck.
- **Not done:** nothing is re-run with other settings.
