# Construct Specification

## Construct ID

`TSM-001`

## Construct Name

Raw 12-1 Time-Series Momentum State

## Mathematical Specification

For each instrument `i` and date `t`:

```text
P_i,t       = adjusted_close_i,t
P_i,t-21    = adjusted_close_i,t-21
P_i,t-252   = adjusted_close_i,t-252
R12_1_i,t   = P_i,t-21 / P_i,t-252 - 1
```

State:

```text
direction_score_i,t = sign(R12_1_i,t)
state_i,t = POSITIVE if direction_score_i,t = +1
state_i,t = NEUTRAL  if direction_score_i,t = 0
state_i,t = NEGATIVE if direction_score_i,t = -1
```

## Validity Conditions

```text
P_i,t > 0
P_i,t-21 > 0
P_i,t-252 > 0
R12_1_i,t is finite
```

## Output Semantics

`POSITIVE` means the instrument's own 12-1 prior adjusted return is above zero.

`NEGATIVE` means the instrument's own 12-1 prior adjusted return is below zero.

`NEUTRAL` means the instrument's own 12-1 prior adjusted return is exactly zero.

## Determinism Requirements

- Input dates must be sorted ascending.
- Tickers must be sorted deterministically.
- Duplicate dates must not create multiple observations.
- Non-positive prices must be treated as missing.
- No random process is permitted.
