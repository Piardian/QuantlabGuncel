# FUND-001 / IM-001

# Implementation Specification

## Implemented Construct

```text
US Financial Commercial Paper Funding Spread Stress
```

## Frozen Formula

```text
FUND-001 = DCPF3M - DTB3
```

## Implementation Files

- `fund001_funding_stress_model.py`
- `feature_pipeline.py`
- `validate_fund_001.py`
- `config.yaml`
- `tests/test_fund001.py`

## Processing Rules

- Load `DCPF3M` and `DTB3`.
- Merge by exact date.
- Do not forward fill official construct values.
- Compute raw spread only when both inputs are present.
- Compute rolling statistics over 252 valid spread observations.
- Emit deterministic output columns and data quality flags.

## Output Columns

- `date`
- `fund001_cp_rate`
- `fund001_tbill_rate`
- `fund001_cp_tbill_spread`
- `fund001_zscore_252d`
- `fund001_percentile_252d`
- `fund001_valid_observation_count_252d`
- `fund001_data_quality_flag`

## Data Quality Flags

- `OK`
- `MISSING_INPUT`
- `INSUFFICIENT_LOOKBACK`
- `ZERO_ROLLING_STD`

## Boundary

This implementation does not evaluate prediction, alpha, trading returns, or economic utility.

