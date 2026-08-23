# Construct Specification

Construct:

**RSM-001 Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank**

Unit of observation:

Security-month.

Residualization:

Monthly excess returns regressed on Fama-French 3 factors over a 36-month rolling window.

Momentum score:

```text
rsm_score = sum(residuals from t-12 through t-2) / std(residuals from t-36 through t-1)
```

Cross-sectional output:

- `rsm_score`
- `rsm_percentile`
- `rsm_state`

State labels:

- TOP_DECILE
- BOTTOM_DECILE
- MIDDLE
- INVALID
