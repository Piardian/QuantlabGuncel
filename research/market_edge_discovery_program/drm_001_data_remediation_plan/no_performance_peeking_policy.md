# No Performance Peeking Policy

## Scope

This policy applies to DRM-001, the remediation implementation work that follows DRM-001, BFL-002 baseline construction, and DBA-002.

## Rule

No performance result may be inspected until the remediated baseline has been frozen and DBA-002 has authorized progression.

## Forbidden Metrics Before DBA-002 Authorization

- CAGR
- Sharpe
- Sortino
- Maximum drawdown
- Profit factor
- Win rate
- Alpha
- Total return
- Benchmark outperformance
- Portfolio profitability
- Any parameter-dependent performance comparison

## Allowed Quality Metrics

The following are allowed because they evaluate data quality rather than alpha:

- Symbol count
- Date coverage
- Missingness
- Duplicate timestamps
- Listing/delisting coverage
- Point-in-time eligibility coverage
- Corporate action coverage
- Data source completeness
- Reproducibility hashes

## Rationale

The purpose of remediation is to remove or disclose material data/bias defects. If performance is inspected during remediation, there is a risk of consciously or unconsciously adjusting the data process to preserve historical results.

## Required Statement For BFL-002

The BFL-002 manifest must include:

```text
alpha_status: UNEVALUATED_AFTER_REMEDIATION
performance_peeking_allowed_before_dba002: false
```
