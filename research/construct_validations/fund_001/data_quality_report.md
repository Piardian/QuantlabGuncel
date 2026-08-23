# FUND-001 / CV-001

# Data Quality Report

## Quality Flag Counts

| data_quality_flag | count | pct_total |
| --- | --- | --- |
| MISSING_INPUT | 12217 | 0.645344 |
| OK | 6463 | 0.341398 |
| INSUFFICIENT_LOOKBACK | 251 | 0.013259 |

## Coverage

- Total rows: 18931
- Full date range: 1954-01-04 to 2026-07-27
- Raw valid spread range: 1997-01-02 to 2026-07-27
- OK normalized range: 1998-01-05 to 2026-07-27

## Main Data Limitation

DTB3 begins much earlier than DCPF3M. Therefore, the merged exact-date output contains many early rows with missing commercial paper input. These rows are correctly marked `MISSING_INPUT` and are not valid FUND-001 observations.

## Validation Interpretation

The missing-data behavior is acceptable because it is explicit, deterministic, and does not forward fill official construct values. The construct should be interpreted over the period where both inputs exist.
