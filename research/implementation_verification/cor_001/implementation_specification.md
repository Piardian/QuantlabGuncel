# COR-001 / IM-001: Implementation Specification

## Frozen Construct

US Equity Market Average Pairwise Correlation State

## Required Implementation

The implementation must reproduce CD-001 exactly:

- daily log returns from adjusted or normalized close prices
- rolling 60-trading-day return window
- complete-window eligibility for each security
- minimum eligible security count of 50
- Pearson correlation matrix across eligible securities
- mean of off-diagonal upper-triangle pairwise correlations
- trailing 252-valid-observation z-score
- trailing 252-valid-observation percentile
- required diagnostics

## Implemented Files

```text
research/constructs/cor_001/cor001_correlation_pipeline.py
research/constructs/cor_001/config.yaml
research/constructs/cor_001/verify_cor001.py
```

## Output Schema

```text
date
cor001_avg_pairwise_corr_60d
cor001_zscore_252d
cor001_percentile_252d
cor001_eligible_security_count
cor001_pair_count
cor001_coverage_ratio
```

## Determinism

No random process is used.

Identical inputs and configuration produce identical output hashes.

