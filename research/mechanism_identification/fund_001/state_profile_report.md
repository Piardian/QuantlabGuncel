# FUND-001 / MI-001

# State Profile Report

## Descriptive State Buckets

State buckets are based on trailing 252-valid-observation percentile:

- `normal_or_low`: percentile <= 50%
- `elevated`: 50% < percentile <= 80%
- `high_stress`: 80% < percentile <= 95%
- `extreme_stress`: percentile > 95%

These are descriptive profiling buckets only. They are not trading rules or optimized thresholds.

## State Profiles

| state_bucket | observations | start | end | mean_cp_rate | mean_tbill_rate | mean_spread | median_spread | mean_zscore | median_zscore | max_zscore | mean_percentile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| normal_or_low | 3089 | 1998-01-05 | 2026-07-27 | 2.269123 | 2.090890 | 0.178232 | 0.110000 | -0.785470 | -0.715090 | 0.136472 | 0.228267 |
| elevated | 1691 | 1998-01-08 | 2026-06-26 | 2.309243 | 2.028551 | 0.280692 | 0.170000 | 0.250391 | 0.249733 | 0.979473 | 0.656840 |
| high_stress | 1026 | 1998-04-28 | 2026-07-02 | 2.423197 | 2.013879 | 0.409318 | 0.280000 | 1.225313 | 1.185669 | 2.581618 | 0.877150 |
| extreme_stress | 657 | 1998-06-01 | 2026-07-16 | 2.232557 | 1.672161 | 0.560396 | 0.360000 | 2.779526 | 2.504315 | 12.706966 | 0.980153 |

## Interpretation

Higher-state buckets show wider average spreads and higher z-scores by construction. The mechanism question is whether widening comes mainly from commercial paper rate elevation, Treasury bill rate decline, or both. That is addressed in `component_decomposition.csv` and `mechanism_label_summary.csv`.
