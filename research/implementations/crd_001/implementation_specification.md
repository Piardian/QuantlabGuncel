# Implementation Specification

## Implemented Construct

CRD-001: US High-Yield Credit Spread Stress.

## Source Series

```text
BAMLH0A0HYM2
```

## Frozen Parameters

```text
normalization_window = 252
max_forward_fill_calendar_days = 5
```

## Implementation Files

- `crd001_credit_stress.py`
- `validate_crd_001.py`
- `config.yaml`
- `tests/test_crd001.py`

## Output Columns

```text
date
crd001_hy_oas
crd001_zscore_252d
crd001_percentile_252d
crd001_valid_observation_count_252d
crd001_days_since_last_observation
crd001_data_quality_flag
```

## Fidelity Statement

The implementation follows the CD-001 frozen definition. It does not add variables, tune windows, modify the source series, run trading strategies, or evaluate predictive or economic value.

