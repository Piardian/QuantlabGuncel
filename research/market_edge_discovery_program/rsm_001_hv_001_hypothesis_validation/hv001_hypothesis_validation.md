# RSM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the MI-001 mechanism hypotheses for the frozen RSM-001 residual momentum construct.

No future returns, alpha, trading performance, backtests, forecasting, parameter optimization or economic value were evaluated.

## Evidence Base

- Source state file: `output/rsm_001/rsm001_residual_momentum_state.csv`
- Valid observations: 66,112
- Unique tickers: 493
- Valid months: 2014-02-28 to 2025-12-31

## Hypothesis Results

### H1

TOP_DECILE states represent persistently positive factor-residual intermediate-horizon performance.

- Classification: **Supported by evidence**
- TOP_DECILE residual_sum_12_1 mean: 0.363251
- Positive rate: 1.000000
- Positive years with positive median: 12/12
- 95% bootstrap CI for mean: [0.357889, 0.368844]

### H2

BOTTOM_DECILE states represent persistently negative factor-residual intermediate-horizon performance.

- Classification: **Supported by evidence**
- BOTTOM_DECILE residual_sum_12_1 mean: -0.371662
- Negative rate: 1.000000
- Negative years with negative median: 12/12
- 95% bootstrap CI for mean: [-0.375838, -0.367075]

### H3

RSM states are related to, but distinguishable from, raw 12-1 cross-sectional momentum states.

- Classification: **Supported by evidence**
- Median monthly Spearman RSM vs raw momentum: 0.750397
- Median TOP_DECILE Jaccard vs raw momentum top decile: 0.342466

### H4

Residual volatility standardization materially affects cross-sectional state assignment relative to unstandardized residual sums.

- Classification: **Supported by evidence**
- Median TOP_DECILE Jaccard standardized vs unstandardized: 0.593220
- Median BOTTOM_DECILE Jaccard standardized vs unstandardized: 0.543860

## Overall HV-001 Conclusion

**Supported by evidence**

The evidence supports the explanatory interpretation that RSM-001 is a factor-residual cross-sectional winner-loser state construct. H3 and H4 support that it is related to, but not identical with, raw momentum or unstandardized residual ranking.
