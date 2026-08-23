# EXB-002 Frozen Specification Alignment

## Frozen TSM-001 Specification

| Parameter | Frozen Value | Current Value | Status |
| --- | ---: | ---: | --- |
| formation_anchor_trading_days | 252 | 252 | PASS |
| skip_period_trading_days | 21 | 21 | PASS |
| direction_threshold | 0.0 | 0.0 | PASS |
| volatility_scaling | excluded | excluded | PASS |

## Formula Alignment

Frozen formula:

```text
tsm_return_12_1_i,t = adjusted_close_i,t-21 / adjusted_close_i,t-252 - 1
tsm001_direction_score_i,t = sign(tsm_return_12_1_i,t)
```

Current implementation continues to use the same formula and same sign convention.

## Alignment Decision

SPEC_IMPLEMENTATION_ALIGNMENT = PASS

FROZEN_PARAMETER_DIFF = NONE

ALPHA_LOGIC_CHANGED = NO
