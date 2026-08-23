# Analysis Plan

## Study Name

WEV-002: Workflow Economic Validation

## Required Analyses

1. Frozen input verification
2. Common sample reconstruction
3. Non-overlap labeling for in-sample and OOS windows
4. Workflow portfolio construction using fixed equal-weight rules
5. Benchmark portfolio construction using fixed equal-weight rules
6. Use-case evaluation
7. Horizon analysis using predefined horizons
8. Risk and downside analysis
9. Turnover proxy analysis
10. Year-by-year stability
11. OOS stability check
12. Final economic utility classification

## Predefined Horizons

Use exactly the same horizons already used in CSM/TSM validation:

- 21 trading days
- 63 trading days
- 126 trading days

No horizon may be added after execution begins.

## Required Metrics

For every use case and benchmark:

- observations
- date count
- ticker count
- mean forward return
- median forward return
- positive return rate
- volatility of forward returns
- downside deviation
- mean drawdown proxy if available
- turnover proxy
- benchmark-relative spread
- year stability
- OOS classification

## Minimum Evidence Standard

Economic Utility Supported requires:

- Improvement versus relevant benchmark in at least two predefined horizons.
- Directionally stable evidence across multiple years.
- OOS evidence does not contradict in-sample evidence.
- Result is not driven by unavailable or empty conflict regions.

Economic Utility Partially Supported requires:

- Some economically favorable evidence, but limitations remain.

Economic Utility Not Supported requires:

- No favorable economic difference versus benchmarks.

Inconclusive requires:

- Insufficient data, unstable evidence, or contradictory evidence.
