# 30 years of the Nasdaq-100 with the scheduled-news calendar, and 11 years of the ORB rules

On 2026-11-18 the user asked: "Can you study the market for the last 30 years with news and all?" On 2026-11-19
they said "go ahead with the 30-year study". Part 1 (below) is:
- **Prices:** daily Nasdaq-100, 1996-11-19 → 2026-11-18 (7,547 trading days).
- **Scheduled news:** Fed decisions, CPI releases and jobs reports.

The questions and rules were committed before any statistic was computed: [`history30/PREREG.md`](history30/PREREG.md),
commit d062f99 at 10:43 ET. The script is [`history30/study.py`](history30/study.py) and every table it printed is in
[`history30/results.md`](history30/results.md).

**Nothing here changes the paper-trading rules.** These are screening results on daily data, not proof of anything about
the ORB options trade, and not a forecast.

## What "news" could and couldn't cover

- **Covered:** the dates of scheduled news.
  - Fed decision days 1996–2026, from the Fed's own calendar pages: 239 days, scheduled meetings only.
  - CPI and jobs-report days 2008–2026, from the BLS release archive: 223 and 219 trading days.
- **Not covered:** what the news *said*. No free archive of 30 years of headlines exists, and Alpaca's archive on this account starts only in April 2026.
- **CPI and jobs start in 2008, not 1996.** The older BLS archive file names aren't always the release date: two checked
  were wrong by up to 12 days. Rather than guess those dates, I left 1994–2007 out.
- **No intraday data.** Everything is daily: open, high, low, close. A "big day" is a full-day range over 1.25× the median of the previous 20 days, the same idea as the morning vol call but for the whole day. On the 40 recent sessions where both exist, the daily label matched the morning (9:30–12:00) label 75% of the time.

## Data checks

- **No bad rows:** no Nasdaq-100 or QQQ rows failed the sanity checks (missing prices, high below low, open or close outside the day's range).
- **Opens before 2001 are unusable.** In 1996–2000 the Nasdaq-100's daily "open" equals the prior close on 15–81% of days, apparently filled in by the data vendor.
  So everything about gaps and open-to-close moves uses 2001–2026 only.
- **QQQ's early data is wrong, not the index.** Nasdaq-100 vs QQQ daily returns correlate 0.996 from 2005 on, but only 0.964 in 1999–2004. On the worst days, QQQ disagrees with both the Nasdaq-100 and the Nasdaq Composite. For example, on 2000-01-07 QQQ shows +12.4%, the Nasdaq-100 +5.7% and the Composite +4.2%. So Yahoo's early QQQ prices are bad and the index is fine, which is why the study uses the index.
- **Release days the market was closed:** BLS published on 8 Good Fridays, when stocks were closed. Those days aren't counted.

## What it found

**1. Fed, CPI and jobs days: none of the three counts as a reliable pattern.** The pre-registered bar was |t| ≥ 2 in
every decade or half.

- **Fed decision days** were big days 41% of the time vs 29% on quiet days (t = +3.8), and the Nasdaq-100 rose 0.37% on average vs 0.05% (t = +3.0).
  - Both effects come from the last two decades. In 1996–2006 the big-day rate was 31% vs 28% (t = +0.6).
  - The extra return was significant only in 2006–2016.
  - The decision comes out at 2:00–2:15pm ET, after the ORB's morning window. On the decision morning itself, gaps were *smaller* than usual (0.49% vs 0.57%).
- **Jobs-report days** were big days 37% of the time vs 29% (t = +2.4 over 2008–2026). Event days beat quiet days in 16 of 19 years.
  - Each half on its own falls short: t = +1.5 and +1.8.
  - This is the closest to a real effect. The report lands at 8:30am, so it shows up in the opening gap and the morning.
- **CPI days** looked like any other day: big days 31% vs 29% (t = +0.6), and CPI days beat quiet days in only 8 of 19 years.

**2. Opening gaps neither continue nor reverse reliably.** Gaps of every size were sorted by direction, 2001–2026:
- Open-to-close moved with the gap on 46–64% of days. No size bucket had |t| ≥ 2 over the whole period.
- The one bucket that reached t = +2.4 in one decade (up gaps of 1–2% in 2006–2016) went the other way in 2001–2006 (t = −1.8).
- Small gaps usually touch the prior close during the day: about 65% for 0.25–0.5% gaps. Big gaps rarely do: 24–29% for 2%+ gaps. That's descriptive, not a trade signal.
- The ORB trades the breakout of the first 5 minutes, not the gap, so nothing here argues for changing it.

**3. Volatility clusters, and that holds in every decade. A one-word "high" call still mostly loses to always saying "normal".**

| Known before the open | Chance of a big day |
|---|---|
| Any day | 30% |
| Yesterday was a big day | 42% (vs 25% after a normal day) |
| Yesterday's VIX close more than 10% *above* its 20-day median | 51% |
| VIX within 10% of its median | 28% |
| VIX more than 10% *below* its median | 13% |
| VIX level ≥ 30 | 35% (VIX < 15: 27%; the level itself says little) |
| CPI, jobs or Fed day (2008+) | 37% (vs 29%) |
| Gap of 1% or more (2001+) | 38% (vs 28%) |

- **Holds in every decade:** "yesterday big" and the VIX jump, with t between 4.7 and 13.8. That's volatility clustering, a long-known market fact. Daily volatility clusters, which inflates t-stats, but these hold decade by decade.
- **Doesn't hold in every decade:** the gap condition, at t = +1.3 in 2001–2006.
- **The pre-registered rule failed.** The rule called HIGH if yesterday was big, or the gap was 1%+, or a CPI/jobs/Fed day.
  - Accuracy: 59% (2008–2017) and 61% (2017–2026), against 69–70% for always saying "normal".
  - On my 18 scored morning calls it got 6 right. My calls got 9 and always-"normal" also got 9.
  - Why: big days are only 30% of days, so a "high" call only beats "normal" when the odds are above 50%. Of everything tested, only the VIX jump reaches that, and barely, at 51%.

## What this means (proposals only; nothing has changed)

- **My morning vol call has no skill so far.** 9 of 18 right, the same as never calling "high". The 30-year base rate
  says a "high" call needs strong evidence. Most of my "high" calls came on days with a 1%+ gap or right after a big day,
  which the history says isn't enough on its own (38–42% odds).
- **A candidate to track, not adopt:** "vol HIGH only when yesterday's VIX close was more than 10% above its 20-day
  median." I picked it after seeing this data, so it has to prove itself on new days.
  - **How:** log it next to my call each morning from now on, then compare both after 20+ new days.
  - **Status:** that would change the morning routine, so I'll only do it if you say so.
- **Fed days** need no ORB change, since the decision lands after the morning trade. **Jobs-report mornings** are worth
  checking with minute data. Part 2 below did: the ORB did no better on event days.

## Part 2: the live ORB rules on 11 years of QQQ 5-minute bars (2016–2026)

The questions were fixed in [`history30/PREREG2.md`](history30/PREREG2.md) (commit 2386118) before the data was downloaded.
The script is [`history30/orb10.py`](history30/orb10.py); every table is in [`history30/results2.md`](history30/results2.md)
and every trade is in [`history30/orb10_trades.csv`](history30/orb10_trades.csv). The signal and exits run through
`paper_orb.py`, the same code that scores the paper trades.

**Headlines weren't available.** Alpaca's news archive on this account starts 2026-04-29, not 2015 as I had expected,
so the "news" here is the Fed/CPI/jobs calendar from part 1.

**Data:**
- 2,736 sessions, 2016-01-04 → 2026-11-18, none dropped.
- Each day's last 5-minute close was within 0.1% of Yahoo's daily close on 98.4% of days. The worst was 0.84%, on 2020-03-13, a chaotic closing auction.
- 2,180 Monday–Thursday signals, plus 549 on Fridays.

**1. Shares (no model): no edge.**

| | Trades | Win rate | Mean per trade | t |
|---|---|---|---|---|
| 2016-01 → 2026-11 | 2,180 | 45% | +0.015R | +0.7 |
| 2016-01 → 2021-06 | 1,104 | 43% | −0.028R | −0.9 |
| 2021-07 → 2026-11 | 1,076 | 47% | +0.059R | +1.8 |

Losing years: 6 of 11. The worst was 2020 (−0.12R a trade); the best were 2024–2025 (about +0.10R).

**2. Options (a Black-Scholes estimate): lost money in every year.**
- Over all 2,180 trades: −$128 per $1,000 trade on average (24% winners, t = −14.8).
- Every year was negative, from −$272 a trade in 2016 to −$33 in 2022.
- Exits: stop 813, time 532, breakeven 453, trail 254, target 128.

**Why options lose when shares are flat:** a bought option pays time decay and the bid-ask spread on every trade, so a signal with no edge loses that cost.

**How far to trust the model:**
- **Checked against reality:** on the 11 recent signals where the after-the-fact account has real option prices, the model averaged +27% a trade vs +34% with the real prices. 8 of 11 exits matched. So the model reads somewhat pessimistic.
- **The early years are the most pessimistic:** a fixed 2-cent spread is about 12% of a $0.17 option (2016), but only about 2% of today's $1 option.
- **What that means for recent years:** 2022–2026 lost $33–$108 a trade. Adding back the 6.5-point gap seen on those 11 days (about $65 on $1,000) would put those years near breakeven, from about −$43 to +$32 a trade.
- **Conclusion:** the honest reading is "no evidence the option version makes money", not a precise loss.

**3. News days didn't matter.**
- **Shares:** event days +0.020R vs +0.015R on other days (t = +0.1). The two filters, skipping event days or taking only event days, change nothing.
- **Jobs reports:** they come out on Fridays, so only 6 Monday–Thursday signals fell on a jobs day.
- **Fed decision mornings:** the option model's worst group, 13% winners and −$204 a trade. That fits part 1's finding that mornings before a 2pm decision are quiet. In shares the same days were −0.07R (t = −0.7), which is noise.

**4. The VIX signal from part 1 doesn't help the trade.** Shares made the same with VIX high or low (t = 0.0). Options were at t = +1.0, also noise.
Predictable volatility didn't make the breakout work better.

**5. Fridays** were no different: −0.013R (t = −0.3), and −$133 a trade on the option model.

## What part 2 means

- **The ORB signal we paper trade had no edge over the last 11 years:** +0.015R a trade over 2,180 trades. The last 7
  real-time paper trades (+$1,231) are well within what luck produces in a sample that small.
- **The option version most likely loses money over time.** The model's error band reaches breakeven in recent years, but nothing points to a profit.
- **By your own rule** ("If the results fail, do not start live trading"), this is a failed screen. My recommendation is no
  real money on these rules, even if the 20-trade paper bar is passed. The bar itself is unchanged. Paper trading can keep running
  as a record. Changing or stopping it is your call.

## Every test run (none dropped)

- **Q1:** 12 event-vs-quiet comparisons, plus the year-by-year count for each event.
- **Q2:** 8 gap buckets for the whole period and for each of the three decades.
- **Q3:** 15 conditional big-day rates and the one pre-registered rule, scored in two halves.
- **Robustness:** 33 decade/half splits.
  - Added after the first run, because PREREG's "what would change anything" requires the every-decade check.
  - Same measures, nothing new.
- **Q3b:** the daily-vs-morning label check, and the rule vs my 18 calls.

**Fixes made during the run, all before results were written:**
- **Tie-break on the 2003 Fed calendar:** a 2003-09-15 "Meeting" with only an agenda sat one day before the scheduled 2003-09-16 decision. The rule "a meeting 1–2 days before another is the same meeting" removed it.
- **Code bug:** a missing-value bug in the big-day column crashed the first run.
- **Gap condition fix:** the gap condition first included 1996–2000, whose opens are copies of the prior close. Those years are now blank for gaps.
  - Before the fix, the copied opens counted as zero gaps: first-decade gap test t = +0.8; whole-period rate 38% vs 29%.
  - After: t = +1.3 on 2001–2006; 38% vs 28%.

## Part 3: 14 strategies on QQQ, which has the best edge? (2006–2026)

The user asked: "so can you run different strategies on the QQQ for the last 20 years and see which one has the best edge?"
The list, the textbook settings and the bar were fixed in [`history30/PREREG3.md`](history30/PREREG3.md) (commit 94c2303)
before anything ran. Code: [`history30/strategies20.py`](history30/strategies20.py). Every table:
[`history30/results3.md`](history30/results3.md).

**How the strategies were run:**
- Hold-for-days strategies use 20 years of daily QQQ data with dividends. Intraday strategies use the 11 years of 5-minute bars that exist (2016 on).
- Signals are acted on at the next open.
- Costs are 0.02% per side.
- A real edge needs t ≥ 3.0 after costs (the 5% level corrected for 14 tests) and a positive result in both halves.
- A unit test found one bug before the run: the dividend column clashed with a pandas method name. It was fixed before any result was read.

**No strategy has a real edge. None reached the bar, even before costs.**

| Rank | Strategy | Edge t after costs | Growth/yr (after costs) | Worst drop |
|---|---|---|---|---|
| — | Buy and hold QQQ (benchmark) | — | +15.4% | −53% |
| 1 | IBS < 0.2, hold one day | +1.8 | +8.3% | −22% |
| 2 | 200-day trend filter | +1.6 | +12.0% | −24% |
| 3 | Golden cross (50-day > 200-day) | +1.5 | +13.3% | −29% |
| 4 | 20-day breakout | +1.0 | +6.2% | −21% |
| 5 | RSI(2) pullback | +0.8 | +3.4% | −14% |
| 6 | Turn of the month | +0.1 | +2.7% | −23% |
| 7 | Bollinger reversion | −0.7 | +4.8% | −42% |
| 8 | First-candle ORB to the close (Zarattini & Aziz) | −0.8 | −2.9% | |
| 9 | Overnight only | −1.8 | +0.7% | −35% |
| 10 | Gap fade | −2.2 | −7.5% | |
| 11 | Our 5-min ORB (shares) | −4.7 | −10.8% | |
| 12 | Prior-day high/low sweep reversal (TJR/ICT-style) | −4.9 | −5.3% | |
| 13 | Intraday momentum, last 30 minutes | −5.9 | −9.7% | |
| 14 | Daytime only | −6.7 | −6.3% | −73% |

For hold-for-days strategies, "edge t" is the t of the alpha over buy-and-hold. For intraday ones it is the t of the mean return per trade.

**What stands out:**
- **Owning QQQ beat every strategy on growth.** +15.4% a year over 20 years. Most of it came overnight: before costs, holding only overnight made +11.3% a year and holding only during the day +3.6%.
- **Trend filters are a risk tool, not an edge.**
  - The 200-day filter and the golden cross gave up 2–3 points a year of growth but roughly halved the worst drop (−24% and −29% vs −53%).
  - Their risk-adjusted return (Sharpe 0.79–0.80) was about the same as holding (0.76).
- **Every day-trading rule lost money after costs.** Before costs:
  - Our ORB, intraday momentum and the sweep reversal were flat (t between −0.8 and 0.0).
  - The first-candle ORB from the Zarattini & Aziz paper made +0.03% a trade (t = +2.6), but the 0.04% round-trip cost erased it. A published replication on index data found the same: positive before costs, zero after.
- **Costs:** 0.02% per side is conservative for QQQ shares, where the spread is about 0.0025%. That only matters for the rules that are positive before costs, and even at zero cost none reaches t = 3.0. Options cost far more: the live quotes in our paper trades had spreads near 2% of the premium.

**What part 3 means:**
- The strongest edge in 20 years of QQQ was owning it and holding through the nights.
- The 200-day average or golden cross is the most defensible way to cut the big drawdowns, at the price of some growth.
- No short-term rule tested here, including our ORB and a mechanical version of the TJR/ICT sweep, showed an edge that beats luck.
