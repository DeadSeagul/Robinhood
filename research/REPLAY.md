# Chart-replay practice

These are practice trades on real past charts, with no money involved (the user asked for this on 2026-10-12). `replay.py` picks a random moment on a past trading day and shows the chart **only up to that moment**. I record a call before anything later is shown. Then the tool plays the rest of the day forward and scores the call. Every call is kept in `replay_journal.csv`, so the record carries across sessions.

```bash
research/fetch_data.sh data_cache/yahoo QQQ SPY NVDA TSLA AAPL AMD META MSFT AMZN PLTR   # last ~60 sessions
python3 -I research/replay.py deal                 # random symbol, unused date, random time (60% before 11:30)
python3 -I research/replay.py decide 11 short --stop 512.40 --target 508.00 --tag orb-break --note "why"
python3 -I research/replay.py reveal 11
python3 -I research/replay.py stats
```

**Keeping it honest**
- The date is hidden until the reveal. Each date is used once across all symbols, so a reveal can't leak that day's market direction into a later drill.
- A decision can't be changed after it's recorded, and no new drill can start while one is open. I never open the data files directly.
- **How a call is scored:**
  - Entry is the next bar's open, with 1 bp of slippage on each side.
  - If one bar touches both the stop and the target, the stop counts.
  - There's a time stop (60 minutes by default).
- **Each call is compared to its mirror image:** the same bracket with the direction flipped, which is a coin flip. I only have skill if my calls beat their mirror images by a margin that isn't noise (t ≥ 2 over many drills).
- **Passes are scored too.** Each pass is checked against a default bracket (0.25% stop, 0.50% target, 60 minutes) in both directions, to see whether passing avoided losses or missed winners.
- **What would change the live rules:** a setup tag that holds up over at least 30 drills with t ≥ 2, and then agrees with the daily shadow trades on live QQQ signals. Until then, lessons here are hypotheses.

## Older days: the Robinhood archive

Yahoo serves only the last ~60 sessions of 5-minute bars. By 2026-10-19 every one of those dates had been used or watched live, and each new trading day is watched live for the paper trade. So since 2026-10-19 the drills also draw on older days from Robinhood (`get_equity_historicals`, 5-minute, regular hours), stored in `data_cache/archive/`.

**How the bars stay blind.**
- Claude Code saves a large tool result straight to a file, and only a 2 KB preview reaches the context.
- A helper agent makes the calls and runs `python3 -I research/archive_add.py <saved file> --delete` on each result. That merges the bars into `data_cache/archive/<SYMBOL>_5m.json` (Yahoo's chart format) and prints only dates and counts.
- Nobody reads the bars, and I never see the helper's previews.
- Where Yahoo and the archive both have a date, the archive's bars are used.

**Coverage:** 2026-02-23 → 2026-07-31 for QQQ, SPY, NVDA, TSLA, AAPL, AMD, META, MSFT, AMZN and PLTR. That's 111 sessions each, and 104 fresh drill dates once warm-up days and used dates are taken out.
- Robinhood keeps about eight months of real 5-minute history. Before 2026-02-23 it returns flat, zero-volume filler marked `interpolated`, which `archive_add.py` drops. The start date will move forward over time.
- I left 2025 out on purpose. It falls inside my training data, and I might recognise the big days, such as the April 2025 selloff.
- February–June 2026 is close to my training cutoff. `stats` reports results before and after 2026-07-01 separately so any memory effect would show.

**Rebuilding.** `data_cache/` isn't committed, so a fresh container starts with an empty archive. Check with `python3 -I research/archive_add.py --summary`. If it's empty, give a helper agent this job:

> Load `mcp__Robinhood__get_equity_historicals` with ToolSearch. For each of QQQ SPY NVDA TSLA AAPL AMD META MSFT AMZN PLTR and each window 2026-02-14→04-01, 04-01→05-16, 05-16→07-01, 07-01→08-01 (00:00Z boundaries), call it with interval "5minute", bounds "regular". Each result is saved to a file: run `cd /home/user/Robinhood && python3 -I research/archive_add.py "<path>" --delete` on it. Check the first file's output before going on: it must say `+N bars`; `NO BARS FOUND` or an error means stop and report it. Split a window in half if it's rejected for too many bars. Never retype data that comes back inline, and never open, print or summarise the saved files. Finish with `archive_add.py --summary` and report only that output.

## Scoreboard

| Batch | Drills | Calls | Win rate | Avg R | Mirror-image avg R | Skill vs coin flip | Passes: default long / short |
|---|---|---|---|---|---|---|---|
| 1 (2026-10-12) | 10 | 5 | 0% | −1.06 | +0.86 | −0.96R/call (t = −3.5, n = 5) | −0.36R / −0.19R |
| 2 (2026-10-13) | 10 | 6 | 50% | +0.41 | −0.18 | +0.29R/call (t = 0.6, n = 6) | +1.17R / −1.08R |
| 3 (2026-10-14) | 10 | 7 | 43% | +0.25 | +0.09 | +0.08R/call (t = 0.2, n = 7) | −0.82R / +1.14R |
| 4 (2026-10-15) | 10 | 2 | 50% | +0.35 | −0.60 | +0.47R/call (t = 0.5, n = 2) | −0.39R / −0.23R |
| 5 (2026-10-16) | 7 | 2 | 50% | −0.03 | +0.44 | −0.23R/call (t = −0.2, n = 2) | +1.07R / −0.69R |
| 6 (2026-10-19, archive days) | 10 | 2 | 50% | +0.28 | +0.36 | −0.04R/call (t = −0.0, n = 2) | +0.14R / −0.19R |
| 7 (2026-10-20, archive days) | 10 | 4 | 50% | −0.32 | +0.26 | −0.29R/call (t = −0.6, n = 4) | −0.58R / +0.36R |
| 8 (2026-10-21, archive days) | 10 | 2 | 0% | −0.53 | +0.90 | −0.72R/call (t = −0.9, n = 2) | +0.07R / −0.31R |
| 9 (2026-10-22, three-setup test) | 10 | 3 | 33% | −0.00 | +0.51 | −0.26R/call (t = −0.3, n = 3) | −0.65R / +0.43R |
| 10 (2026-10-23, three-setup test) | 10 | 1 | 100% | +0.34 | −1.05 | +0.70R/call (n = 1) | −0.47R / +0.37R |
| 11 (2026-10-26, three-setup test) | 10 | 1 | 100% | +0.30 | −0.35 | +0.33R/call (n = 1) | −0.13R / −0.25R |
| 12 (2026-10-27, three-setup test) | 10 | 0 | – | – | – | – | −0.37R / +0.15R |
| 13 (2026-10-28, three-setup test) | 10 | 2 | 0% | −1.06 | +0.42 | −0.74R/call (t = −1.0, n = 2) | +0.11R / −0.25R |
| 14 (2026-10-29, three-setup test) | 10 | 2 | 100% | +0.80 | −0.77 | +0.78R/call (n = 2) | +0.31R / −0.71R |
| 15 (2026-10-30, three-setup test) | 10 | 0 | – | – | – | – | −0.31R / −0.12R |
| **All** | **147** | **39** | **41%** | **−0.06** | **+0.17** | **−0.11R/call (t = −0.6): no skill shown** | −0.12R / −0.11R |

**Pre-registered three-setup test** (from drill 78 on, calls only on `range-break`, `retest-entry` and `failed-break-reclaim`; judged after 30 calls): **9 calls, 5 wins, +0.10R total, skill +0.04R per call (t = 0.1).**

## Lessons and hypotheses

**Batch 1 (drills 1–10).**
- **Every call I made was a with-the-move entry, and all five reversed.** The five setups were:
  - a VWAP pullback buy
  - a breakout retest
  - a high-volume new-high breakout
  - a trend-flag short
  - an opening-range breakdown short

  In four of the five, the move had already run into a prior-day level or the day's extreme when I entered. Fading those spots would have won. Five calls is far too few to conclude anything, but the pattern matches the live trades:
  - **10/8:** the QQQ breakdown snapped back.
  - **10/9:** the breakdown stalled.
  - **10/12 (shadow trade):** the breakdown stalled again.
- **My stops sat inside normal noise.** Four stops were placed 0.7–1.0 × the size of a recent 5-minute bar from entry. Two calls went +0.6R and +1.4R in my favour before reversing. Next batch: put stops beyond real structure, such as VWAP or the last swing, and consider taking profit at 1R.
- **Passes were the best decisions.** Mid-range or chop spots would have lost on average with a default trade either way. Passing in the middle of a range around VWAP looks right.
- **Hypotheses to test with tags in the next batches:**
  - `extended-into-level`: after a big bar into a prior-day level, the move reverses more often than it continues.
  - `retest-entry`: waiting for a pullback to the broken level beats entering right on the breakout close.
  - Midday (11:30–14:30) targets set at the day's high or low are too far; about 1.5R is more realistic.

**Batch 2 (drills 11–20)**, using stops beyond real chart levels:
- **Stops beyond structure helped.** All three wins had stops past a real level:
  - drill 12: a retest of yesterday's high
  - drill 13: a range break
  - drill 18: a base with lower highs

  Drill 12 went 0.8R against me before hitting its target; the old tight default stop would have been knocked out (−1.08R).
- **Entering at an extreme after a long run lost in both directions.**
  - Drill 14 faded a stretched trend day at a round number (−1.1R).
  - Drill 15 bought the day's high after a midday grind (−1.0R).

  So `extended-into-level` is not a fade signal on trend days. The better answer to "stretched" is to pass, not to trade against it. This revises the batch 1 hypothesis.
- **What worked:**
  - range breaks that weren't stretched yet (2 of 2, +2.6R)
  - the retest entry (1 of 1, +2.05R)
- **Passes cost upside this batch.** In 3 of the 4 passes, price rallied, and a default long would have made +1.9R each. Two of those had readable signs: a tight morning flag at the high (drill 17), and a failed breakdown that reclaimed the opening-range low (drill 20). Hypothesis to tag: `tight-flag-am` (morning flag right at the day's high, before 10:30) and `failed-break-reclaim`.
- **Running total:** 11 calls, −2.9R. The skill measure is −0.28R per call (t = −0.8), so no edge is shown yet in either direction. It needs about 30 calls before it means anything.

**Batch 3 (drills 21–30).**
- **Time of day is the clearest split so far.**

  | Calls placed | Count | Avg R | Total |
  |---|---|---|---|
  | Before 11:30 | 10 | +0.29 | +2.9R |
  | 11:30–14:30 | 8 | −0.51 | −4.1R |

  The morning edge isn't directional skill, though. Before 11:30, my calls beat their mirror images by only +0.09R (t = 0.2). Morning moves are simply big enough for a 1.5–2R bracket to pay in either direction, which fits the playbook research: the first hour moves 2–3× more than 1:30–2:30pm. Working rule for drills: **no new entries after 11:30.**
- **The setups that keep working:**
  - `retest-entry` 2 of 2 (+3.5R)
  - `failed-break-reclaim` 1 of 1 (+1.4R)
  - `tight-flag-am` 1 of 1 (+1.7R)

  The afternoon version of the flag (`tight-flag-pm`, light volume) lost (−1.1R). `range-break` is now 2 of 3; the loss was a morning short on 0.4× volume. `trend-continuation` is 1 of 5 (−2.75R), and four of those five were midday.
- **Passes:** 2 of 3 missed shorts that a default bracket would have won (+1.9R, +1.35R), both on afternoon fades. No clear rule yet.
- **Running total:** 18 calls, −1.1R, skill −0.14R per call (t = −0.5). Still no proven edge. The setup tags are where the signal will show up if there is one. Each needs about 30 drills before I'd trust it.

**Batch 4 (drills 31–40).** The first batch run by the daily paper-trading task.
- **Eight passes, two calls.** Four drills fell after 11:30 and were passed under the cutoff rule. On average a default trade would have lost on the passes in both directions (long −0.39R, short −0.23R), so passing was right overall.
- **The win:** `vwap-reclaim-hl` (drill 32, AMD, +1.77R). A gap-up flushed on the first bar, then made higher lows back over VWAP. The stop went under the last higher low. The default tight stop would have lost −1.08R on the same trade, so stops beyond structure helped for the third batch running.
- **The loss:** `gap-fail-lower-high` (drill 37, SPY, −1.07R). I shorted a bounce under VWAP while it was still rising, before any rejection. SPY reclaimed VWAP and closed near the day's high. Working rule: **fading at a level needs a rejection bar first** (a close back away from the level), never an entry mid-bounce.
- **Missed winners:**
  - Drill 33 (META): a 50-minute flag above the prior-day high, before 11:00, broke up (default long +1.92R). That is the third morning flag at the highs that resolved upward (drill 17, `tight-flag-am`, drill 33). If the pattern keeps holding, I'll start taking it.
  - Drill 35 (TSLA): I passed a clean opening-range break and retest because yesterday's high was less than 1R away. The stock trended to 341.6 and never came near a stop under the retest low. The default bracket lost only because its stop was too tight.
  - Drill 36 (NVDA): a gap-up that failed below its opening-range low, then put in a lower high at that low (default short +1.92R). This is the same idea that lost in drill 37, but here the rejection had already happened. Both drills stay tagged `gap-fail-lower-high` for now.
- **Running total:** 20 calls, −0.4R, skill −0.08R per call (t = −0.3). Still no edge either way. `retest-entry`, `range-break`, `tight-flag-am` and the reclaim setups are the only tags with positive results, and none has more than three samples.

**Batch 5 (drills 41–47).** Only seven drills: every date in Yahoo's 60-session window is now used or was watched live. From here, about one new date a day becomes available.
- **Win:** `range-break` (drill 44, AAPL, +1.05R at the time stop). It was a 9:45 close above the opening range after a higher low, not stretched, with the stop under VWAP and the prior close. `range-break` is now 3 of 4.
- **Loss:** `flag-above-level` (drill 45, QQQ, −1.10R, stopped on the first bar). The flag sat right where a gap-down had just finished filling to the prior close. Drill 33's flag (a missed winner) had room above it. Working rule: **a completed gap fill is a target, not a launch pad.** Don't buy a flag at the fill level.
- **Passes missed longs.** Four of the five passes would have won as a default long, including three after 11:30 (drills 42, 43, 46). Over all 25 passes, a default long averages +0.10R and a default short −0.29R. That mostly reflects the sample: QQQ rose from about 684 to 720+ over these weeks. It isn't a setup, so the 11:30 cutoff stays, because my own afternoon *calls* are still 1 of 8.
- **Running total:** 22 calls, −0.5R, skill −0.09R per call (t = −0.4). No edge either way.

**Batch 6 (drills 48–57).** The first batch from the Robinhood archive, with dates from April to July 2026.
- **The win:** `range-break` (drill 54, QQQ, +1.62R). A short after the opening-range low broke and price made lower highs under VWAP, with the target at the prior-day low.
- **The loss:** `range-break` (drill 56, AAPL, −1.06R). I bought a pullback after a break of the opening-range high before the pullback had reached the level. `range-break` is now 4 of 6.
- **Entering before the level is tested has now lost twice:** drill 37 shorted a bounce still rising, and drill 56 bought a pullback still falling. Working rule: **wait for price to touch the level and for a bar to close back in the trade's direction.** That's the `retest-entry` rule, which is 2 of 2.
- **Two pass patterns have now been wrong twice each:**
  - *Passing a fresh break of the opening-range high because it's "stretched into the prior-day high."* Drills 35 and 55 (both TSLA) ran straight through that high, and a default long would have made +1.92R both times. The better answer is to wait for the first pullback, not to pass the whole move.
  - *Passing a failed gap-up once the lower high is in.* Drills 36 and 48 kept falling (default short +1.92R each). The only `gap-fail-lower-high` call that lost (drill 37) went in before the rejection.
- **Afternoon passes are fine on average.** Over 16 passes after 11:30, a default long averaged −0.01R and a default short −0.40R. Morning passes cost more: a default long averaged +0.22R over 17 of them.
- **Running total:** 24 calls, +0.1R, skill −0.09R per call (t = −0.4). Still no edge either way.

**Batch 7 (drills 58–67).**
- **The batch 6 idea failed as soon as I traded it.** Batch 6 called `gap-fail-lower-high` a missed opportunity, based on two passes that would have won. Taken as real calls, it's now 0 of 3 (−2.83R): drill 62 timed out at −0.73R, and in drill 66 AMD held the prior-day high and ran +5%. **A pattern found by looking back at passes is hindsight.** Only calls count, so I've dropped it from the candidate setups.
- **Chasing a stretched breakout still doesn't pay.** Drill 64 tested "breaks keep running" (from drills 35 and 55) on TSLA. It scratched (+0.05R), and TSLA later gave back the whole move. `trend-continuation` is 1 of 6.
- **What held up:** `failed-break-reclaim` 2 of 2 (+1.82R; drill 67 PLTR, +0.44R at the time stop). `range-break` 4 of 6 (+3.12R) and `retest-entry` 2 of 2 (+3.47R). Those three tags hold 8 of my 11 winning calls. They're the only setups I'd keep testing, and each still needs about 30 calls.
- **Running total:** 28 calls, −1.2R, skill −0.12R per call (t = −0.5). Still no edge either way.

**Batch 8 (drills 68–77).**
- **The two calls:** `retest-entry` (drill 71, TSLA short, −1.03R; the stock reversed and closed +2% off the low) and `range-break` (drill 77, MSFT short, −0.02R at the time stop). `retest-entry` is now 2 of 3 and `range-break` 4 of 7.
- **30 calls is the mark I set on day one for when the record starts to mean something. It shows no skill.** Total −2.3R, and −0.16R per call against the mirror-image coin flip (t = −0.8).
- **The three setups I keep naming are suggestive at most.** `range-break`, `retest-entry` and `failed-break-reclaim` together are 12 calls, +0.61R average, +0.42R per call over the coin flip, t = 1.2. That's below the t ≥ 2 bar, and I picked these three out of 14 tags after the fact, so the real evidence is weaker than the t suggests. The other 18 calls averaged −0.53R.
- **Next:** keep trading only those three setups in the drills and pass everything else, then judge them on their next 30 calls. That gives the hypothesis a fresh, pre-registered test instead of more hindsight.

**Batch 9 (drills 78–87).** The first batch under the three-setup rule.
- **The three calls:**
  - `range-break` short, drill 81, MSFT, −1.05R. MSFT went on to my target, but only after stopping me out.
  - `range-break` long, drill 85, NVDA, −1.06R. It broke out of an hour-long base, then the day collapsed.
  - `retest-entry` short, drill 87, META, +2.09R. A textbook retest: it tested the opening-range low from below and closed back under it.
- **Tag totals:** `range-break` is now 4 of 9 and `retest-entry` 3 of 4.
- **The rule did what it should:** 7 of the 10 drills had no qualifying setup and were passed. Four of those were after the cutoff.

**Batch 10 (drills 88–97).**
- **The one call:** `failed-break-reclaim` (drill 92, SPY long, +0.34R at the time stop, after reaching +1.13R). A gap-down broke the opening-range low, then closed back above it and VWAP twice. `failed-break-reclaim` is now 3 of 3.
- **The rest:** 9 passes. Six fell after the cutoff or at it. The others were a stretched chase, an unconfirmed retest and a mid-range chop. A default short would have won on 4 of the 9 passes (drills 89, 90, 93, 96), but passes aren't calls, and batch 7 showed that pass patterns are hindsight.

**Batch 11 (drills 98–107).**
- **The one call:** `range-break` (drill 104, TSLA long, +0.30R at the time stop). A tight flag above the opening-range high broke at 10:55, with the stop under the flag low.
- **The rest:** 9 passes. Four were after the cutoff. The others were a whipsaw at the opening-range low, two unconfirmed reclaims, and two stretched or late moves.
- **Passes had mixed hindsight:** a default long averaged −0.13R and a default short −0.25R. The cost: drill 105 (AAPL whipsaw at the range low, then +3%) and drill 99 (afternoon) would have won as default longs.
- **The three-setup test now reads 5 calls, +0.63R.** It's slowly accumulating, but at about one call a day it will take weeks to reach 30.

**Batch 12 (drills 108–117).** No qualifying setup in 10 drills.
- **Why:** four were after the cutoff, two were chop, three were unconfirmed or whipsawing at a level, and two were moves already finished. Drill 108's breakout had run through its gap fill, and drill 113's breakdown closed right on its gap fill.
- **Drill 113 was a miss.** NVDA kept falling from the gap fill to 199. That makes the "don't trade into a completed gap fill" idea 1 of 2 (it held in drill 45).
- **The pace is slow:** the three-setup test has 5 calls after 40 drills, about 1 per 8 drills. Reaching 30 will take roughly 25 more trading days. I'm not loosening the rules mid-test.

**Batch 13 (drills 118–127).** Two `retest-entry` calls, both stopped.
- **Drill 118, PLTR long, −1.04R.** A failed break below the opening-range low was reclaimed, and the 10:25 bar wicked through VWAP to 134.10 and closed back above. My stop sat at 134.05, just under that wick. The next bar's low was exactly 134.05, then PLTR ran to 137.88. The flipped bracket also lost, so the problem was the stop distance, not the direction. Hypothesis for after the test: give a retest stop some room beyond the wick. I'm not changing stop rules mid-test.
- **Drill 127, SPY short, −1.08R.** On a gap-down, the 9:45 bar retested up through the opening-range low and closed back under it, a textbook retest by my definition. SPY then reversed and closed +0.5% from my entry, while the flipped bracket made +1.88R. That's the same failure as drill 85: a clean setup on a day that turned.
- **The rest:** 8 passes. Four were after the cutoff, two were whipsaws at the opening-range low, and two were stretched moves (an AAPL breakdown and an AMD two-bar thrust through the opening-range high). AMD kept running to 548, but chasing stretched breaks has not paid (drill 64), so the pass stands.
- **The three-setup test now reads 7 calls, 3 wins, −1.49R** (skill −0.18R per call, t = −0.4). That's noise either way at n = 7. It gets judged at 30 calls.

**Batch 14 (drills 128–137).** Two `range-break` longs, both won, both at the time stop.
- **Drill 133, AMZN, +0.44R.** It made the first close above the opening-range high after a 90-minute base, 0.25% past the level. I put the stop under VWAP and the base rather than at the breakout wick. It reached +0.86R, then AMZN gave the whole move back in the afternoon.
- **Drill 137, NVDA, +1.15R.** It made the first close above the opening-range high at 9:45, 0.23% past the level and above VWAP, with the stop just under the breakout bar. It reached +1.56R.
- **What they share:** both broke out within about 0.25% of the level, and both stops sat a little beyond the structure rather than at a wick. That fits batch 13's hypothesis about stop room, but two drills aren't evidence, and no rule changes mid-test.
- **The rest:** 8 passes. Three were after the cutoff, three were stretched (an MSFT break already 1.2% past the level, an AMZN flag and an AMD flush), and two were whipsaws at a level.
- **Tag totals:** `range-break` is now 7 of 12, +2.88R.
- **The three-setup test now reads 9 calls, 5 wins, +0.10R** (skill +0.04R per call). That's flat and still noise. It gets judged at 30 calls.

**Batch 15 (drills 138–147).** No qualifying setup in 10 drills, the second empty batch (batch 12 was the first).
- **Why:** six were at or after the 11:30 cutoff. The other four were a pullback that hadn't reached its level, an hour-long base broken by only 15 cents, 90 minutes of chop inside the opening range, and an hour of chop after a reclaim I'd already missed.
- **Passing cost nothing on average:** a default long would have averaged −0.31R and a default short −0.12R. MSFT (drill 144) did fall to 371 after the marginal base break I passed, so its default short got stopped out (−0.54R) before the move.
- **The deal is the bottleneck:** about 40% of drills land after the cutoff by design, and those are automatic passes. The three-setup test stays at 9 calls after 70 drills. At about one call per 8 drills, the remaining 21 calls need roughly 160 more drills, or about 16 more trading days. I'm not changing the deal or the rules mid-test.
