# Part 2: the ORB rules on 11 years of QQQ 5-minute bars, fixed before running

Written 2026-11-19 before any of the data below was downloaded. The user got an Alpaca key for this ("I've got them").
Part 1 is [PREREG.md](PREREG.md) / [../HISTORY30.md](../HISTORY30.md).

**What the key turned out to cover** (checked with one request each, before writing this):
- QQQ 1-minute and 5-minute SIP bars from 2016-01-04 on.
- Alpaca's headline archive on this account starts 2026-04-29. The earlier plan expected 2015, so **this part can't use headlines**. The "news" is the scheduled calendar from part 1 (FOMC, CPI, jobs), plus the VIX signal part 1 found.

## Data

- **QQQ 5-minute bars:** Alpaca `v2/stocks/QQQ/bars`, `timeframe=5Min`, `feed=sip`, `adjustment=split`, 2016-01-04 → 2026-11-18. Regular hours only (bars starting 9:30–15:55 ET).
- **Volatility:** ^VXN (Nasdaq-100 volatility index) and ^VIX daily closes from Yahoo. Only the prior day's close is used.
- **Checks before results:**
  - **Bad sessions:** sessions without a 9:30 bar, or with fewer than 40 regular-hours bars, are dropped. The number dropped is reported.
  - **Cross-check:** the last 5-minute close of each day vs Yahoo's QQQ daily close (2016+). Report the share within 0.1%, and the worst days.

## The rules: the live paper rules, run by the same code

- **Signal:** `paper_orb.signal`, the first 5-minute close beyond the 9:30 bar's range, on a bar starting by 11:25. Entry is at the next bar's open.
- **Days:** Monday–Thursday, as live. Friday signals are reported on their own line and kept out of the totals.
- **A. Shares (no model):** `paper_orb.share_trade`.
  - Exits: stop at the other side of the opening range, 2R target, and an exit 90 minutes after entry.
  - A bar touching both stop and target counts as the stop.
  - Result in R (multiples of the risk).
- **B. Options (a model, an estimate only):** a hypothetical next-day QQQ option, priced with Black-Scholes.
  - **Volatility:** flat, equal to the prior day's VXN close. Interest rate 4%.
  - **Spread:** mid ± $0.01, so the ask is mid + 0.01 and the bid mid − 0.01.
  - **Price cap:** the cap scales with QQQ's price, at 0.15% of QQQ at entry. That's about $1.00 at today's $660; a fixed $1 would be a near-the-money option in 2016, when QQQ was $110.
  - **Contract:** the call (long) or put (short) on a $1 strike grid, nearest the money, whose model ask is ≤ the cap.
  - **Size:** floor($1,000 / (ask × 100)) contracts, with $0.09 fees per contract.
  - **Option bars:** each QQQ 5-minute bar becomes an option bar. Open and close come from QQQ's open and close. The high comes from QQQ's favorable extreme and the low from its adverse extreme.
  - **Exits:** `paper_orb.option_trade`, current rules.
    - **Stop:** when QQQ touches the share stop, the option sells at the bar's low.
    - **Target:** 2× entry, any print fills.
    - **Trail:** arms at 1.5×, sells at 1.3×.
    - **Breakeven:** arms at 1.25×, sells at the entry.
    - **Time:** 90 minutes after entry.
  - **What the model gets wrong:**
    - No volatility skew, and no change in implied volatility during the trade. Real puts usually gain IV in a selloff, so puts are probably understated and calls overstated.
    - Daily QQQ expiries only exist from late 2022. Before that, the "next-day option" is hypothetical.

## Questions

1. **Shares (A):** trades, win rate, mean R with t, total R. Also by year and by half: 2016-01 → 2021-06 and 2021-07 → 2026-11.
2. **Options (B):** the same measures in $ per $1,000 trade, plus the share of each exit reason.
3. **News days:** A and B split by what was scheduled on the trade day: jobs, CPI, FOMC, none. Two filters, scored against "take every signal":
   - (a) skip CPI/jobs/FOMC days;
   - (b) take only those days.
4. **VIX state** (the part 1 signal): A and B split by prior-day VIX ratio: < 0.9, 0.9–1.1, > 1.1.
5. **Fridays:** A and B for Friday signals, which the live rules skip.

**What counts:** |t| ≥ 2 overall and the same sign in both halves. Otherwise the result reads as noise. Nothing changes the
paper rules automatically. A filter that passes would go to the user as a proposal, and would first be tracked on new
days. Every number is reported, and nothing is tuned.
