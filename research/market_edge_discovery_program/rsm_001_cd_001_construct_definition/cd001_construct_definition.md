# RSM-001 / CD-001 Construct Definition

## Purpose

Freeze one precise, reproducible Residual Momentum construct definition based on LR-001.

No implementation, backtesting, optimization, predictive validation, economic validation or alpha claim was performed.

## Frozen Construct

Construct ID:

**RSM-001**

Construct Name:

**Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank**

Primary construct:

RSM-001 measures cross-sectional momentum using each security's prior residual returns after removing common Fama-French 3-factor exposure.

## Factor Model

Frozen residualization model:

```text
excess_return_i,t =
    alpha_i
    + beta_mkt_i * MKT_RF_t
    + beta_smb_i * SMB_t
    + beta_hml_i * HML_t
    + residual_i,t
```

Required factor inputs:

- `MKT_RF`
- `SMB`
- `HML`
- `RF`

## Return Frequency

Frozen return frequency:

**Monthly**

Security returns and factor returns must be aligned by month.

## Regression Window

Frozen regression window:

**36 months**

Minimum valid observations:

**24 months**

If fewer than 24 valid monthly observations are available, the security-month is invalid.

## Formation Window

Frozen residual momentum formation:

**12-1**

Definition:

Use residual returns from months `t-12` through `t-2`, excluding the most recent month `t-1`.

## Residual Momentum Score

For security `i` at month `t`:

```text
residual_sum_12_1_i,t = sum(residual_i,t-12 ... residual_i,t-2)

residual_vol_36m_i,t = standard_deviation(residual_i,t-36 ... residual_i,t-1)

rsm_score_i,t =
    residual_sum_12_1_i,t / residual_vol_36m_i,t
```

Residual volatility standardization is included by definition.

## Construct Output

RSM-001 is a **cross-sectional ranking construct**.

For every valid month:

```text
rsm_percentile_i,t = percentile_rank(rsm_score_i,t within valid universe at month t)
```

State labels:

```text
TOP_DECILE      if percentile >= 0.90
BOTTOM_DECILE   if percentile <= 0.10
MIDDLE          otherwise
INVALID         if required data is unavailable
```

## Explicit Exclusions

Excluded from RSM-001:

- CAPM residualization.
- Fama-French 5-factor residualization.
- Industry residualization.
- Daily return residualization.
- Non-standard regression windows.
- Non-standard formation windows.
- Future returns.
- Portfolio construction.
- Transaction costs.
- Economic value.
- Optimized thresholds.

These may be studied later only as separate preregistered constructs or comparators.

## Final CD-001 Status

**Construct frozen**

RSM-001 is now frozen as a Fama-French 3-factor standardized 12-1 residual momentum rank construct.

Progression to IM-001 requires monthly adjusted security returns and monthly Fama-French factor returns.
