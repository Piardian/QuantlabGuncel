# COR-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the explanatory mechanism identified in MI-001 is empirically supported.

This study evaluates explanatory validity only.

It does not evaluate prediction, trading performance, alpha, profitability, or economic value.

## Construct

COR-001 measures average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

## State Definitions

The MI-001 descriptive state definitions were preserved:

- `LOW_CORRELATION`: `cor001_percentile_252d <= 0.20`
- `MID_CORRELATION`: `0.20 < cor001_percentile_252d < 0.80`
- `HIGH_CORRELATION`: `cor001_percentile_252d >= 0.80`

These are explanatory analysis buckets, not trading thresholds.

## Statistical Method

For each preregistered hypothesis, HV-001 compared LOW_CORRELATION and HIGH_CORRELATION observations using:

- mean difference
- bootstrap confidence interval
- Cohen's d
- fixed-seed permutation test for mean difference
- cross-period direction consistency
- trimmed-extreme robustness

Only same-day or trailing observable variables were used.

## Hypothesis Results

| Hypothesis | Variable | Expected | Difference: High - Low | Cohen's d | Permutation p | Classification |
| --- | --- | --- | ---: | ---: | ---: | --- |
| H1 | SPY 20d realized volatility | High > Low | 0.1539 | 1.5476 | 0.0002 | Supported by evidence |
| H2 | SPY 52w drawdown | High < Low | -0.0808 | -1.6699 | 0.0002 | Supported by evidence |
| H3 | BRD-001 breadth | High < Low | -0.2815 | -1.7485 | 0.0002 | Supported by evidence |
| H4 | COR-001 raw correlation | High > Low | 0.2399 | 2.6336 | 0.0002 | Supported by evidence |

## Interpretation

The evidence supports the MI-001 mechanism:

```text
COR-001 represents market-wide synchronization / common co-movement stress.
```

The strongest external explanatory evidence comes from H1-H3:

- High COR-001 states correspond to higher contemporaneous realized market volatility.
- High COR-001 states correspond to deeper contemporaneous market drawdowns.
- High COR-001 states correspond to weaker contemporaneous market breadth.

## Important Methodological Note

H4 is partly construct-internal because HIGH_CORRELATION and LOW_CORRELATION are defined using COR-001's own percentile.

Therefore H4 confirms that the state split produces materially separated synchronization states, but the stronger explanatory evidence comes from H1-H3.

## Cross-Period Evidence

Across four broad historical blocks, all tested mechanism differences preserved the expected direction:

- 2011-2014
- 2015-2018
- 2019-2022
- 2023-2025

This supports cross-period consistency of the explanatory mechanism.

## Robustness Evidence

After trimming the top and bottom 1% of each tested variable within high and low groups, all hypotheses preserved the expected direction.

## Final HV-001 Conclusion

COR-001 / HV-001 is classified as:

```text
Supported by evidence
```

This conclusion is limited to explanatory validity.

No predictive, economic, trading, profitability, alpha, or production-deployment conclusion is made.

