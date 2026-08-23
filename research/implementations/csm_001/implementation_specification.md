# CSM-001 / IM-001 Implementation Specification

## Construct

`CSM-001` - Canonical 12-1 Cross-Sectional Momentum State.

## Frozen Formula

```text
return_12_1_i,t = adjusted_close_i,t-21 / adjusted_close_i,t-252 - 1
```

```text
csm001_momentum_score_i,t = percentile_rank(return_12_1_i,t among eligible universe_t)
```

```text
csm001_top_decile_flag_i,t = 1 if csm001_momentum_score_i,t >= 0.90 else 0
```

## Implementation Files

- `feature_pipeline.py`: deterministic feature builder.
- `csm001_momentum_model.py`: frozen model wrapper.
- `validate_csm_001.py`: synthetic verification script.
- `config.yaml`: frozen parameter/configuration file.

## Frozen Parameter Guards

The implementation raises `ValueError` if the formation anchor, skip period, top-decile threshold, or minimum eligible count differs from CD-001.

## CD-001 Parameter Mapping

| CD-001 field | Implementation field | Frozen value |
| --- | --- | ---: |
| `formation_anchor_trading_days` | `formation_anchor_trading_days` | 252 |
| `skip_period_trading_days` | `skip_period_trading_days` | 21 |
| `top_decile_threshold` | `top_decile_threshold` | 0.90 |
| `minimum_eligible_securities_per_date` | `minimum_eligible_count` | 50 |
| `rank_tie_method` | `method="average"` | average |

## Boundary

Implementation does not run strategies, evaluate predictive power, measure returns, optimize parameters, or claim alpha.
