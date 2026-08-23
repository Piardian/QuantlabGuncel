# ISM-001 / HV-001 Hypothesis Validation

## Purpose

Formally validate the MI-001 mechanism hypotheses for the frozen ISM-001 industry momentum construct.

No future returns, alpha, trading performance, backtests, forecasting, parameter optimization, economic value or stock-level signal assignment was evaluated.

## Evidence Base

- Source state file: `output/ism_001/ism001_industry_momentum_state.csv`
- Valid observations: 55,285
- Unique industries: 49
- Valid months: 1927-07-31 to 2026-05-31

## Hypothesis Results

### H1

TOP_DECILE states represent industries with persistently high intermediate-horizon relative industry performance.

- Classification: **Supported by evidence**
- TOP_DECILE 12-1 formation mean: 0.466493
- TOP minus MIDDLE mean: 0.352253
- Years with positive TOP_DECILE median: 96/100
- 95% bootstrap CI for mean: [0.456561, 0.476189]

### H2

BOTTOM_DECILE states represent industries with persistently low intermediate-horizon relative industry performance.

- Classification: **Supported by evidence**
- BOTTOM_DECILE 12-1 formation mean: -0.151016
- BOTTOM minus MIDDLE mean: -0.265256
- Years with BOTTOM_DECILE median below full middle median: 95/100
- 95% bootstrap CI for mean: [-0.156563, -0.145666]

### H3

ISM-001 states are rotating leadership / laggard classifications rather than static industry identity labels.

- Classification: **Supported by evidence**
- Industries that appeared in TOP_DECILE at least once: 1.000000
- TOP_DECILE one-month retention: 0.725414

### H4

Cross-sectional industry dispersion is a necessary observable condition for meaningful ISM-001 state separation.

- Classification: **Supported by evidence**
- Median monthly p90-p10 12-1 formation spread: 0.364299
- 95% bootstrap CI for p90-p10 spread median: [0.355059, 0.370346]
- Median monthly TOP minus BOTTOM mean spread: 0.544209

## Overall HV-001 Conclusion

**Supported by evidence**

The evidence supports the explanatory interpretation that ISM-001 represents a rotating industry-level intermediate-horizon leadership / laggard state with persistent tail states and substantial cross-sectional industry dispersion.
