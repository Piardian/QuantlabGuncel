# OPT-001 / CV-001

# Distribution Analysis

## Raw VIX Distribution

- Mean VIX: 19.4427
- Median VIX: 17.6100
- 95th percentile VIX: 32.9400
- Maximum VIX: 82.6900

## Normalized Output Distribution

- Mean z-score over OK observations: -0.0395
- Z-score standard deviation over OK observations: 1.2545
- Mean rolling percentile over OK observations: 0.4654

## Diagnostic Buckets

| feature | bucket | count | pct_ok |
| --- | --- | --- | --- |
| opt001_percentile_252d | 0-10 | 1635 | 0.181909 |
| opt001_percentile_252d | 10-20 | 944 | 0.105029 |
| opt001_percentile_252d | 20-30 | 788 | 0.087672 |
| opt001_percentile_252d | 30-40 | 779 | 0.086671 |
| opt001_percentile_252d | 40-50 | 717 | 0.079773 |
| opt001_percentile_252d | 50-60 | 747 | 0.083111 |
| opt001_percentile_252d | 60-70 | 729 | 0.081108 |
| opt001_percentile_252d | 70-80 | 773 | 0.086004 |
| opt001_percentile_252d | 80-90 | 733 | 0.081553 |
| opt001_percentile_252d | 90-100 | 1143 | 0.127170 |
| opt001_zscore_252d | <=-2 | 40 | 0.004450 |
| opt001_zscore_252d | -2_to_-1 | 1878 | 0.208945 |
| opt001_zscore_252d | -1_to_0 | 3557 | 0.395750 |
| opt001_zscore_252d | 0_to_1 | 1940 | 0.215843 |
| opt001_zscore_252d | 1_to_2 | 965 | 0.107365 |
| opt001_zscore_252d | >=2 | 608 | 0.067646 |

## Interpretation

The distribution is right-tailed, which is expected for an options-implied volatility level. Rolling percentile and z-score transformations provide normalized state representations while preserving the raw VIX level as the primary construct observation.
