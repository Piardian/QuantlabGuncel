# OPT-001 / IM-001

# Implementation Specification

## Implemented Construct

```text
US Equity Index Option-Implied Volatility State
```

## Frozen Source

```text
VIXCLS
```

## Implementation Files

- `opt001_options_implied_model.py`
- `feature_pipeline.py`
- `validate_opt_001.py`
- `config.yaml`
- `tests/test_opt001.py`

## Processing Rules

- Load `VIXCLS`.
- Do not forward fill official construct values.
- Treat missing or non-positive values as invalid.
- Compute rolling statistics over 252 valid VIX observations.
- Emit deterministic output columns and data quality flags.

## Output Columns

- `date`
- `opt001_vix_close`
- `opt001_zscore_252d`
- `opt001_percentile_252d`
- `opt001_valid_observation_count_252d`
- `opt001_data_quality_flag`

## Data Quality Flags

- `OK`
- `MISSING_INPUT`
- `INSUFFICIENT_LOOKBACK`
- `ZERO_ROLLING_STD`
- `INVALID_NON_POSITIVE`

## Boundary

This implementation does not evaluate prediction, alpha, trading returns, or economic utility.

