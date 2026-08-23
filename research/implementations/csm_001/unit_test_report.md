# CSM-001 / IM-001 Unit Test Report

## Test Command

```powershell
.\.venv\Scripts\python.exe research\implementations\csm_001\validate_csm_001.py
```

## Result

```text
rows: 19200
valid_rows: 4080
first_valid_date: 2020-12-18
last_valid_date: 2021-03-23
deterministic_hash: 947b47a93527c0384dcfc75750d2cad2227dee03368c8e4d78b2e32dbf5d556c
status: PASSED
```

## Status

`PASSED`

## Guard Coverage

The validation script verifies frozen-parameter rejection for both `formation_anchor_trading_days` and `minimum_eligible_count`.
