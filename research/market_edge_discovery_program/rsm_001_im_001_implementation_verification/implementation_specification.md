# Implementation Specification

## Source Files

- `research/implementations/rsm_001/feature_pipeline.py`
- `research/implementations/rsm_001/rsm001_residual_momentum_model.py`
- `research/implementations/rsm_001/config.yaml`
- `research/implementations/rsm_001/validate_rsm_001.py`

## Inputs

Monthly security returns:

- Index: month-end date.
- Columns: ticker symbols.
- Values: monthly returns.

Monthly factor returns:

- Index: month-end date.
- Columns: `mkt_rf`, `smb`, `hml`, `rf`.

Factor column names are normalized to lowercase internally.

## Outputs

The output schema includes:

- `month`
- `ticker`
- `monthly_return`
- `rf`
- `mkt_rf`
- `smb`
- `hml`
- `excess_return`
- `residual_return`
- `residual_sum_12_1`
- `residual_vol_36m`
- `rsm_score`
- `rsm_rank`
- `rsm_eligible_count`
- `rsm_percentile`
- `rsm_state`
- `rsm_valid_observation`

## Frozen Parameters

- Regression window: 36 months.
- Minimum observations: 24.
- Formation start lag: 12 months.
- Formation end lag: 2 months.
- Residual volatility window: 36 months.
- Top decile threshold: 0.90.
- Bottom decile threshold: 0.10.

