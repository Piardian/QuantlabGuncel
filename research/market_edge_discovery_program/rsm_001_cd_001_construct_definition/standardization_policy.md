# Standardization Policy

RSM-001 includes residual volatility standardization.

Formula:

```text
rsm_score = residual_sum_12_1 / residual_vol_36m
```

Residual volatility window:

36 months through `t-1`.

If residual volatility is zero, missing or non-finite:

The observation is INVALID.

Rationale:

Standardization improves comparability of residual momentum scores across securities and aligns with the risk-adjusted nature of residual momentum.
