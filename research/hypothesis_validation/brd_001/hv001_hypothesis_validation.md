# BRD-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the explanatory mechanism identified in MI-001 is empirically supported.

This study evaluates explanatory validity only.

It does not evaluate prediction, trading performance, alpha, profitability, or economic value.

## Construct

BRD-001 measures the percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above its own 200-day simple moving average.

## State Definitions

The MI-001 descriptive state definitions were preserved:

- `LOW_BREADTH`: bottom 20% of valid BRD-001 observations
- `MID_BREADTH`: middle 60%
- `HIGH_BREADTH`: top 20%

Observed cutoffs:

- LOW_BREADTH cutoff: 0.5265
- HIGH_BREADTH cutoff: 0.8172

These are explanatory analysis buckets, not trading thresholds.

## Statistical Method

For each preregistered hypothesis, HV-001 compared LOW_BREADTH and HIGH_BREADTH observations using:

- mean difference
- bootstrap confidence interval
- Cohen's d
- fixed-seed permutation test for mean difference
- cross-period direction consistency

Only same-day or trailing observable variables were used.

## Hypothesis Results

| Hypothesis | Variable | Expected | Difference: High - Low | Cohen's d | Permutation p | Classification |
| --- | --- | --- | ---: | ---: | ---: | --- |
| H1 | BRD-001 breadth | High > Low | 0.5061 | 5.8122 | 0.0002 | Supported by evidence |
| H2 | SPY distance from SMA200 | High > Low | 0.1423 | 3.4179 | 0.0002 | Supported by evidence |
| H3 | SPY 20d realized volatility | High < Low | -0.1529 | -1.5251 | 0.0002 | Supported by evidence |
| H4 | SPY 52w drawdown | High > Low | 0.1069 | 2.5879 | 0.0002 | Supported by evidence |
| H5 | SPY above SMA200 | High > Low | 0.7950 | 2.7826 | 0.0002 | Supported by evidence |

## Interpretation

The evidence supports the MI-001 mechanism:

```text
BRD-001 represents long-term cross-sectional trend participation and internal market confirmation.
```

The evidence also supports the secondary characterization:

```text
LOW_BREADTH states correspond to weak index trend condition, elevated realized volatility and deeper contemporaneous drawdown.
```

## Important Methodological Note

H1 is partly construct-internal because LOW_BREADTH and HIGH_BREADTH are defined using BRD-001 itself.

Therefore H1 confirms that the descriptive state split produces a materially separated participation regime, but the stronger explanatory evidence comes from H2-H5.

## Cross-Period Evidence

Across four broad historical blocks, all tested mechanism differences preserved the expected direction:

- HIGH_BREADTH showed stronger SPY trend condition.
- HIGH_BREADTH showed lower realized volatility.
- HIGH_BREADTH showed shallower drawdown.
- HIGH_BREADTH showed higher SPY-above-SMA200 frequency.

However, the 2022-2025 block had only 14 HIGH_BREADTH observations, so period-balance limitations remain.

## Final HV-001 Conclusion

BRD-001 / HV-001 is classified as:

```text
Supported by evidence
```

This conclusion is limited to explanatory validity.

No predictive, economic, trading, profitability, alpha, or production-deployment conclusion is made.

