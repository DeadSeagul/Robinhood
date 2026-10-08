# Backtest report

Data source: yahoo (unofficial, research only). Universe: 63 symbols fixed in advance (63 usable). Start equity $25,000. Every variant was run exactly once with parameters fixed before the run.

## Summary (all costs included)

| Variant | Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | Costs | t (mean R) | 95% CI mean R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1_orb15_retest_2R | 10 | 30% | $111.57 | $-58.17 | $-7.25 (-0.21R) | 0.82 | -0.98 | -0.72% | $-72.48 | $51.51 | -0.45 | [-1.08, +0.73] |
| V2_orb15_retest_no_target | 10 | 20% | $221.84 | $-58.45 | $-2.40 (-0.14R) | 0.95 | -0.19 | -0.71% | $-23.96 | $56.82 | -0.21 | [-1.17, +1.35] |
| V3_orb15_breakout_close_2R | 20 | 25% | $96.32 | $-55.19 | $-17.31 (-0.42R) | 0.58 | -2.64 | -1.75% | $-346.30 | $104.50 | -1.45 | [-0.96, +0.17] |
| V4_orb5_retest_2R | 14 | 50% | $105.40 | $-60.38 | $22.51 (+0.33R) | 1.75 | 2.26 | -0.74% | $315.09 | $62.96 | +0.80 | [-0.45, +1.09] |

## V1_orb15_retest_2R

Period 2026-08-13 to 2026-10-08 (40 trading days after a 20-day warm-up).

| Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | Costs | t (mean R) | 95% CI mean R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 30% | $111.57 | $-58.17 | $-7.25 (-0.21R) | 0.82 | -0.98 | -0.72% | $-72.48 | $51.51 | -0.45 | [-1.08, +0.73] |

Benchmarks: SPY buy-and-hold -0.13% (max DD -3.05%); no-trade 0.00%. Strategy -0.29%.

Screen: **FAIL** — only 10 trades (< 100); expectancy $-7.25 per trade is not positive after costs; profit factor 0.82 < 1.2; t-stat of mean R -0.45 < 2.0 (not statistically credible)

Chronological folds (fixed parameters, each fold out-of-sample):

| Fold | Dates | Trades | Net profit | Expectancy R | Profit factor |
|---|---|---|---|---|---|
| 1 | 2026-08-13 to 2026-09-01 | 2 | $44.77 | +0.44 | 1.72 |
| 2 | 2026-09-02 to 2026-09-21 | 5 | $62.36 | +0.06 | 1.38 |
| 3 | 2026-09-22 to 2026-10-08 | 3 | $-179.61 | -1.10 | 0.00 |

Where it made and lost money:

| Bucket | Trades | Net P/L | Avg R |
|---|---|---|---|
| trend: SPY down day | 3 | $2.17 | -0.20 |
| trend: SPY up day | 7 | $-74.65 | -0.22 |
| vol: high-range day | 9 | $-30.10 | -0.08 |
| vol: low-range day | 1 | $-42.38 | -1.45 |
| symbol: AMD | 1 | $-62.21 | -1.11 |
| symbol: CRM | 1 | $106.96 | +1.94 |
| symbol: CRWD | 2 | $52.33 | +0.45 |
| symbol: GOOGL | 1 | $-60.81 | -1.11 |
| symbol: IWM | 1 | $-42.38 | -1.45 |
| symbol: META | 2 | $52.60 | +0.45 |
| symbol: MSFT | 1 | $-56.56 | -1.14 |
| symbol: NKE | 1 | $-62.41 | -1.08 |

Scanner: 137 candidate-days out of 2520 symbol-days. Signals proposed: 18. Rule violations: 0.

Skipped/rejected setups by reason:

- breakout ignored: 186
- retest ignored: 20
- breakout failed: 15
- skipped: 3
- entry not triggered in time: 3
- no liquidity in the fill bar: 1
- extended: 1
- reward/risk to prior-day high 247.50 is 0.44 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.07 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.81 < 2.0: 1

## V2_orb15_retest_no_target

Period 2026-08-13 to 2026-10-08 (40 trading days after a 20-day warm-up).

| Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | Costs | t (mean R) | 95% CI mean R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 20% | $221.84 | $-58.45 | $-2.40 (-0.14R) | 0.95 | -0.19 | -0.71% | $-23.96 | $56.82 | -0.21 | [-1.17, +1.35] |

Benchmarks: SPY buy-and-hold -0.13% (max DD -3.05%); no-trade 0.00%. Strategy -0.10%.

Screen: **FAIL** — only 10 trades (< 100); expectancy $-2.40 per trade is not positive after costs; profit factor 0.95 < 1.2; t-stat of mean R -0.21 < 2.0 (not statistically credible)

Chronological folds (fixed parameters, each fold out-of-sample):

| Fold | Dates | Trades | Net profit | Expectancy R | Profit factor |
|---|---|---|---|---|---|
| 1 | 2026-08-13 to 2026-09-01 | 2 | $-123.12 | -1.09 | 0.00 |
| 2 | 2026-09-02 to 2026-09-21 | 5 | $278.77 | +0.81 | 2.69 |
| 3 | 2026-09-22 to 2026-10-08 | 3 | $-179.61 | -1.10 | 0.00 |

Where it made and lost money:

| Bucket | Trades | Net P/L | Avg R |
|---|---|---|---|
| trend: SPY down day | 3 | $-165.23 | -1.21 |
| trend: SPY up day | 7 | $141.27 | +0.31 |
| vol: high-range day | 9 | $17.92 | +0.00 |
| vol: low-range day | 1 | $-41.89 | -1.45 |
| symbol: AMD | 1 | $-62.21 | -1.11 |
| symbol: CRM | 1 | $-60.94 | -1.11 |
| symbol: CRWD | 2 | $77.00 | +0.67 |
| symbol: GOOGL | 1 | $-60.81 | -1.11 |
| symbol: IWM | 1 | $-41.89 | -1.45 |
| symbol: META | 2 | $243.85 | +2.11 |
| symbol: MSFT | 1 | $-56.56 | -1.14 |
| symbol: NKE | 1 | $-62.41 | -1.08 |

Scanner: 137 candidate-days out of 2520 symbol-days. Signals proposed: 18. Rule violations: 0.

Skipped/rejected setups by reason:

- breakout ignored: 186
- retest ignored: 20
- breakout failed: 15
- skipped: 3
- entry not triggered in time: 3
- no liquidity in the fill bar: 1
- extended: 1
- reward/risk to prior-day high 247.50 is 0.44 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.07 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.81 < 2.0: 1

## V3_orb15_breakout_close_2R

Period 2026-08-13 to 2026-10-08 (40 trading days after a 20-day warm-up).

| Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | Costs | t (mean R) | 95% CI mean R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 25% | $96.32 | $-55.19 | $-17.31 (-0.42R) | 0.58 | -2.64 | -1.75% | $-346.30 | $104.50 | -1.45 | [-0.96, +0.17] |

Benchmarks: SPY buy-and-hold -0.13% (max DD -3.05%); no-trade 0.00%. Strategy -1.39%.

Screen: **FAIL** — only 20 trades (< 100); expectancy $-17.31 per trade is not positive after costs; profit factor 0.58 < 1.2; t-stat of mean R -1.45 < 2.0 (not statistically credible)

Chronological folds (fixed parameters, each fold out-of-sample):

| Fold | Dates | Trades | Net profit | Expectancy R | Profit factor |
|---|---|---|---|---|---|
| 1 | 2026-08-13 to 2026-09-01 | 5 | $31.21 | +0.15 | 1.17 |
| 2 | 2026-09-02 to 2026-09-21 | 8 | $-163.56 | -0.45 | 0.52 |
| 3 | 2026-09-22 to 2026-10-08 | 7 | $-213.95 | -0.81 | 0.28 |

Where it made and lost money:

| Bucket | Trades | Net P/L | Avg R |
|---|---|---|---|
| trend: SPY down day | 9 | $-319.38 | -0.86 |
| trend: SPY up day | 11 | $-26.92 | -0.07 |
| vol: high-range day | 15 | $-228.52 | -0.38 |
| vol: low-range day | 5 | $-117.78 | -0.57 |
| symbol: AMD | 1 | $70.94 | +1.33 |
| symbol: ARM | 1 | $107.74 | +1.98 |
| symbol: COST | 1 | $-55.59 | -1.10 |
| symbol: CRM | 2 | $-125.72 | -1.05 |
| symbol: CRWD | 1 | $114.76 | +1.98 |
| symbol: DDOG | 1 | $-47.93 | -1.07 |
| symbol: GM | 2 | $-109.56 | -1.20 |
| symbol: GOOGL | 1 | $-63.44 | -1.10 |
| symbol: IWM | 2 | $-80.60 | -1.37 |
| symbol: JPM | 1 | $-50.14 | -1.35 |
| symbol: META | 1 | $84.12 | +1.57 |
| symbol: MSTR | 1 | $104.03 | +1.96 |
| symbol: NKE | 1 | $-59.21 | -1.08 |
| symbol: ORCL | 1 | $-59.93 | -1.03 |
| symbol: PFE | 1 | $-61.86 | -1.07 |
| symbol: TSLA | 1 | $-58.92 | -1.05 |
| symbol: UNH | 1 | $-54.98 | -1.23 |

Scanner: 137 candidate-days out of 2520 symbol-days. Signals proposed: 59. Rule violations: 0.

Skipped/rejected setups by reason:

- breakout ignored: 211
- extended: 37
- skipped: 36
- reward/risk to prior-day high 247.50 is 0.25 < 2.0: 2
- reward/risk to prior-day high 155.00 is 0.31 < 2.0: 1
- reward/risk to prior-day high 247.50 is 1.65 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.49 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.23 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.43 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.47 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.59 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.77 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.21 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.10 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.01 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.18 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.32 < 2.0: 1
- reward/risk to prior-day high 247.50 is 0.16 < 2.0: 1
- reward/risk to prior-day high 203.33 is 0.81 < 2.0: 1
- reward/risk to prior-day high 326.00 is 0.41 < 2.0: 1

## V4_orb5_retest_2R

Period 2026-08-13 to 2026-10-08 (40 trading days after a 20-day warm-up).

| Trades | Win rate | Avg win | Avg loss | Expectancy | Profit factor | Sharpe | Max DD | Net profit | Costs | t (mean R) | 95% CI mean R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 14 | 50% | $105.40 | $-60.38 | $22.51 (+0.33R) | 1.75 | 2.26 | -0.74% | $315.09 | $62.96 | +0.80 | [-0.45, +1.09] |

Benchmarks: SPY buy-and-hold -0.13% (max DD -3.05%); no-trade 0.00%. Strategy +1.26%.

Screen: **FAIL** — only 14 trades (< 100); t-stat of mean R 0.80 < 2.0 (not statistically credible)

Chronological folds (fixed parameters, each fold out-of-sample):

| Fold | Dates | Trades | Net profit | Expectancy R | Profit factor |
|---|---|---|---|---|---|
| 1 | 2026-08-13 to 2026-09-01 | 4 | $282.12 | +1.21 | 5.54 |
| 2 | 2026-09-02 to 2026-09-21 | 5 | $221.68 | +0.71 | 2.81 |
| 3 | 2026-09-22 to 2026-10-08 | 5 | $-188.72 | -0.74 | 0.21 |

Where it made and lost money:

| Bucket | Trades | Net P/L | Avg R |
|---|---|---|---|
| trend: SPY down day | 6 | $-187.58 | -0.65 |
| trend: SPY up day | 8 | $502.67 | +1.07 |
| vol: high-range day | 13 | $377.23 | +0.44 |
| vol: low-range day | 1 | $-62.14 | -1.07 |
| symbol: COST | 1 | $49.20 | +0.86 |
| symbol: CRM | 1 | $111.25 | +1.95 |
| symbol: CRWD | 1 | $115.90 | +1.97 |
| symbol: INTC | 1 | $115.06 | +1.96 |
| symbol: IWM | 1 | $-50.68 | -1.36 |
| symbol: META | 2 | $51.90 | +0.46 |
| symbol: MRNA | 1 | $-63.24 | -1.05 |
| symbol: NKE | 1 | $-63.36 | -1.09 |
| symbol: ORCL | 1 | $-63.23 | -1.09 |
| symbol: PANW | 1 | $116.73 | +1.98 |
| symbol: SMCI | 1 | $117.12 | +1.97 |
| symbol: TGT | 1 | $-62.14 | -1.07 |
| symbol: UNH | 1 | $-59.41 | -1.29 |

Scanner: 159 candidate-days out of 2520 symbol-days. Signals proposed: 24. Rule violations: 0.

Skipped/rejected setups by reason:

- breakout ignored: 266
- breakout failed: 36
- retest ignored: 35
- extended: 14
- entry not triggered in time: 6
- skipped: 2
- reward/risk to prior-day high 331.85 is 1.31 < 2.0: 1
- reward/risk to prior-day high 331.85 is 0.38 < 2.0: 1
- reward/risk to prior-day high 331.85 is 0.98 < 2.0: 1
- reward/risk to prior-day high 331.85 is 1.16 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.07 < 2.0: 1
- reward/risk to prior-day high 329.87 is 1.81 < 2.0: 1
