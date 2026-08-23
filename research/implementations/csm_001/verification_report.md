# CSM-001 / IM-001 Verification Report

## Verification Status

`PASSED`

## Checks Performed

- Output schema matches expected CSM-001 schema.
- Execution is deterministic on identical synthetic input.
- Momentum scores are bounded between 0 and 1.
- Valid observations respect minimum eligible count.
- Highest cross-sectional return receives score 1.0.
- Lowest cross-sectional return receives score 0.0.
- Frozen parameter guard rejects modified formation anchor.
- Frozen parameter guard rejects modified minimum eligible count.

## Validation Output

```text
rows: 19200
valid_rows: 4080
first_valid_date: 2020-12-18
last_valid_date: 2021-03-23
deterministic_hash: 947b47a93527c0384dcfc75750d2cad2227dee03368c8e4d78b2e32dbf5d556c
status: PASSED
```

## Boundary

Verification uses synthetic data only and does not evaluate market predictive validity or economic utility.
