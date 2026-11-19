# 30-year daily study: questions fixed before running

Written 2026-11-19, before any of the statistics below were computed. The commit time of this file is the proof.
The user asked on 2026-11-18: "Can you study the market for the last 30 years with news and all?" and said on
2026-11-19 "go ahead with the 30-year study". This is part 1 (daily prices plus the scheduled-news calendar).
Part 2 (minute bars and headlines from 2015–2016, needing an Alpaca key) is separate.

Nothing here changes the paper-trading rules. Results are reported in full in `../HISTORY30.md`, including the ones
that show nothing. These are screening results, not proof of future profitability.

## Data

| Series | Source | Use |
|---|---|---|
| Nasdaq-100 index (^NDX), daily OHLC | Yahoo chart API, `interval=1d`, `period1/period2` | All price statistics, 1996-11-19 → 2026-11-18 (the last 30 years) |
| QQQ, daily OHLC | Yahoo | Only a cross-check of ^NDX (daily returns should correlate > 0.99 from 1999) |
| VIX (^VIX), daily close | Yahoo | Volatility input (prior day's close only) |
| Scheduled FOMC decision days | federalreserve.gov `fomchistoricalYYYY.htm` (1996–2020) and `fomccalendars.htm` (2021–2026), parsed by `build_calendar.py` | Event days. Only scheduled meetings; conference calls, unscheduled meetings, notation votes and cancelled meetings are left out because they weren't known in advance. The decision day is the meeting's last day. A "Meeting" one or two days before another is treated as one meeting (2003-09-15 had only an agenda; the decision was 2003-09-16). Result: 8 a year, 7 in 2020. |
| CPI release days | BLS CPI release archive (bls.gov/bls/news-release/cpi.htm), links from 2008-02 on, whose file names carry the release date | Event days, 2008-02-20 → 2026-11-10 |
| Jobs report (Employment Situation) days | BLS archive (bls.gov/bls/news-release/empsit.htm), links from 2008-02 on | Event days, 2008-02-01 → 2026-11-06 |

Why CPI and jobs start in 2008: the older BLS archive file names are not always the release date. Two checked against
the release text were wrong: `empsit_01192000` was released Friday, January 7, 2000 and `empsit_070997` on Thursday,
July 3, 1997. The 2008+ names were spot-checked against six releases' embargo lines and all six matched
(CPI 2010-08-13, 2015-03-24, 2025-12-18; jobs 2008-07-03, 2013-10-22, 2026-02-11). Rather than guess the
1994–2007 dates, they're left out. bls.gov blocks scripted downloads from this environment (HTTP 403), so the
link lists were read with the web-fetch tool and checked twice.

**Data checks, run before the statistics:**
- Drop days with a missing open, high, low or close, or with high < low, or open or close outside [low, high]. Report how many.
- **Opens:** a calendar year's ^NDX opens count as usable for open-based statistics (gap, open-to-close) only if fewer
  than 5% of its days have open equal to the prior close (to the cent). Old index data sometimes fills the open with
  the prior close. Years that fail are excluded from those statistics and listed.
- Cross-check ^NDX against QQQ daily returns from 1999-03-10.

## Definitions (all inputs known before the open of the day they describe)

- `ret` = close / prior close − 1. `range` = (high − low) / prior close. `gap` = open / prior close − 1.
  `intraday` = close / open − 1.
- **Big day** = range > 1.25 × the median range of the previous 20 trading days. This mirrors the morning news call's
  "vol high", but on the full day, since daily data has no morning range.
- **VIX ratio** = prior day's VIX close / median of the 20 VIX closes before that.
- Statistics: means with Welch t-stats. Daily volatility clusters, which makes t-stats look stronger than they are, so a
  result also has to hold in most individual years (or in each decade) to count. |t| < 2 means indistinguishable from noise.

## Questions

**Q1. Scheduled news days vs quiet days.** For each event type (FOMC 1996-11 → 2026-11; CPI and jobs 2008-02 → 2026-11),
compare event days with quiet days (none of the three events, same period) on: big-day rate, mean range, mean |gap|,
mean ret. Also the share of years in which event days' mean range beat quiet days'.
Note: FOMC decisions come out at 2:00–2:15pm ET, after the morning trading window; CPI and jobs at 8:30am, before the open.

**Q2. Do opening gaps continue or reverse?** Days with usable opens, by gap size |gap|: 0.25–0.5%, 0.5–1%, 1–2%, ≥ 2%,
up and down separately. For each: count, share of days where open-to-close moves the gap's way (continuation), mean
open-to-close move signed by the gap's direction (with t), and the share of days that touch the prior close (gap fill).
Also split by decade: 1996-11 → 2006-11, 2006-11 → 2016-11, 2016-11 → 2026-11.

**Q3. Can a big day be called before the open?** Big-day rate overall and conditional on, one at a time:
prior day big (yes/no); VIX ratio (< 0.9, 0.9–1.1, > 1.1); VIX level (< 15, 15–20, 20–30, ≥ 30);
scheduled CPI/jobs/FOMC day (2008+); |gap| ≥ 1%.
Then **one** pre-registered rule, no tuning: **call HIGH if the prior day was big, or |gap| ≥ 1%, or a CPI, jobs or
FOMC decision is scheduled today.** Score it on 2008-02 → 2017-06 and 2017-06 → 2026-11 separately: accuracy against
"always normal", the share of HIGH calls that were big days, and the share of big days it caught.

**Q3b. Does it transfer to the morning call?**
- On the cached QQQ 5-minute bars (about 60 sessions, 2026-08-26 on), how often the daily "big" label agrees with the
  morning (9:30–12:00) one.
- On every scored day in `../news_log.csv`, the rule's call vs my logged vol call against the scored morning outcome.

## What would change anything

Nothing changes automatically. A result would only become a proposal to the user if it holds in every decade or half
and has |t| ≥ 2. Even then, the morning vol call would change only if the rule also beats my calls on the logged
news days, and the user agrees.
