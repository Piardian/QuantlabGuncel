# Implementation Specification

## Construct

ISM-001 is implemented as a monthly industry-level cross-sectional rank construct.

## Required Inputs

| Input | Source | Frequency | Notes |
|---|---|---:|---|
| Ken French 49 industry portfolio returns | Ken French Data Library | Monthly | Value-weighted return section only |

## Required Outputs

| Field | Meaning |
|---|---|
| `month` | Month-end timestamp |
| `industry_id` | Stable parsed Ken French industry identifier |
| `industry_name` | Industry name carried from the source column |
| `industry_return` | Monthly industry portfolio return in decimal form |
| `industry_return_12_1` | Compounded lagged return from t-12 through t-2 |
| `ism_rank` | Cross-sectional average rank |
| `ism_eligible_count` | Number of valid industries in that month |
| `ism_score` | Percentile rank scaled from 0 to 1 |
| `ism_state` | `TOP_DECILE`, `BOTTOM_DECILE`, `MIDDLE` or `INVALID` |
| `ism_valid_observation` | Boolean valid-observation marker |

## Frozen Parameters

- `formation_start_lag_months = 12`
- `formation_end_lag_months = 2`
- `minimum_valid_industries = 30`
- `top_decile_threshold = 0.90`
- `bottom_decile_threshold = 0.10`
- Rank tie method: average rank.

## Files

- `research/implementations/ism_001/feature_pipeline.py`
- `research/implementations/ism_001/ism001_industry_momentum_model.py`
- `research/implementations/ism_001/prepare_ism_001_data.py`
- `research/implementations/ism_001/run_ism001_construct_generation.py`
- `research/implementations/ism_001/validate_ism_001.py`
- `research/implementations/ism_001/config.yaml`
