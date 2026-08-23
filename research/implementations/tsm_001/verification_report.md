# TSM-001 / IM-001 Verification Report

## Verification Status

`PASSED`

## Checks Performed

- Output schema matches expected TSM-001 schema.
- Execution is deterministic on identical synthetic input.
- Positive prior return maps to `+1` and `POSITIVE`.
- Negative prior return maps to `-1` and `NEGATIVE`.
- Zero prior return maps to `0` and `NEUTRAL`.
- All-missing series produces no valid observations.
- Frozen formation anchor guard rejects modified value.
- Frozen volatility-scaling guard rejects inclusion.

## Boundary

Verification uses synthetic data only and does not evaluate market predictive validity or economic utility.

## Validation Output

```text
rows: 1600
valid_rows: 272
first_valid_date: 2020-12-18
last_valid_date: 2021-03-23
deterministic_hash: e3b1f6348935adb092e299fc54cd41b3bf309af282e6ab177dcbb40fd33244d9
status: PASSED
```
