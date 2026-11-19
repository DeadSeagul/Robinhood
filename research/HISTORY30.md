# 30 years of the Nasdaq-100 with the scheduled-news calendar (part 1)

On 2026-11-18 the user asked: "Can you study the market for the last 30 years with news and all?" On 2026-11-19
they said "go ahead with the 30-year study". This is part 1:
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
- **Not covered:** what the news *said*. No free archive of 30 years of headlines exists. Part 2 (with an Alpaca key) would add headlines from 2015 on.
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
  watching in part 2 with minute data.

## What part 2 would add

- **Minute data:** the real ORB rules (stop, 2× target, trail, breakeven, 90-minute exit) run on about 10 years of QQQ minute bars.
- **Headlines:** 2015 on.
- **Scope:** that's the test that bears on the trade itself.
- **Needs:** a free Alpaca account, with the key entered in a secure form, never in chat. Option prices still don't exist that far back, so option P&L would be estimated from QQQ's moves.

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
