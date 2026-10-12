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

## Scoreboard

| Batch | Drills | Calls | Win rate | Avg R | Mirror-image avg R | Skill vs coin flip | Passes: default long / short |
|---|---|---|---|---|---|---|---|
| 1 (2026-10-12) | 10 | 5 | 0% | −1.06 | +0.86 | −0.96R/call (t = −3.5, n = 5) | −0.36R / −0.19R |

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
