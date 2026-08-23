# TSM-001 / IM-001 Implementation Specification

## Construct

`TSM-001` - Raw 12-1 Time-Series Momentum State.

## Frozen Formula

```text
tsm_return_12_1_i,t = adjusted_close_i,t-21 / adjusted_close_i,t-252 - 1
```

```text
tsm001_direction_score_i,t = sign(tsm_return_12_1_i,t)
```

## Implementation Files

- `feature_pipeline.py`: deterministic feature builder.
- `tsm001_momentum_model.py`: frozen model wrapper.
- `validate_tsm_001.py`: synthetic verification script.
- `config.yaml`: frozen parameter/configuration file.

## Frozen Parameter Guards

The implementation raises `ValueError` if formation anchor, skip period, direction threshold, or volatility scaling differs from CD-001.

## Boundary

Implementation does not run strategies, evaluate predictive power, optimize parameters, measure returns, or claim alpha.
