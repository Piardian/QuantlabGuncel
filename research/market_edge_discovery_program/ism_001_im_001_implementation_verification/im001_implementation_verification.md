# ISM-001 / IM-001 Implementation Development & Verification

## Purpose

Implement the frozen CD-001 construct:

**Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank**

This is an implementation fidelity study only. No predictive validity, alpha, trading performance, economic value, portfolio construction or production recommendation was evaluated.

## Frozen Implementation

The implementation follows CD-001 exactly:

```text
industry_return_12_1_j,t =
    product(1 + industry_return_j,t-12 ... 1 + industry_return_j,t-2) - 1

ism_score_j,t =
    percentile_rank(industry_return_12_1_j,t within valid industries at month t)
```

## Data

- Source: Ken French 49 Industry Portfolios monthly value-weighted returns.
- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_CSV.zip
- Parsed source file: `data/ism_001/ken_french_49_industry_value_weighted_monthly.csv`
- Rows: 1,199 monthly observations.
- Columns: 49 industry portfolios.
- Date range: 1926-07-31 to 2026-05-31.

## Generated Artifact

- Construct state file: `output/ism_001/ism001_industry_momentum_state.csv`
- Rows: 58,751
- Valid observations: 55,285
- Unique industries: 49
- First valid month: 1927-07-31
- Last valid month: 2026-05-31
- Persisted artifact hash: `fb492d61a7aa6e279564b658a08cf764f642b8d43f482c0a33801584cfa645e7`

## Verification Result

**Successfully implemented**

The implementation is deterministic, schema-stable and faithful to the frozen CD-001 specification. This conclusion is limited to implementation readiness and does not imply predictive or economic validity.
