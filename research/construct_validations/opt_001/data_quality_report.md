# OPT-001 / CV-001

# Data Quality Report

## Quality Flag Counts

| data_quality_flag | count | pct_total |
| --- | --- | --- |
| OK | 8988 | 0.942040 |
| MISSING_INPUT | 302 | 0.031653 |
| INSUFFICIENT_LOOKBACK | 251 | 0.026308 |

## Coverage

- Total rows: 9,541
- Full date range: 1990-01-02 to 2026-07-28
- Raw valid observations: 9,239 (96.83%)
- OK normalized observations: 8,988 (94.20%)
- Missing input rows: 3.17%
- Insufficient lookback rows: 2.63%

## Main Data Limitation

VIXCLS contains non-trading-day and source availability gaps. These rows are explicitly flagged as `MISSING_INPUT`. The first 251 valid VIX observations are explicitly flagged as `INSUFFICIENT_LOOKBACK` because the frozen construct requires 252 valid observations before normalized z-score and percentile values are emitted.

## Validation Interpretation

The missing-data behavior is acceptable for research use because it is explicit, deterministic, and avoids forward filling official construct values.
