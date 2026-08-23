# FUND-001 / IM-001

# Unit Test Report

## Test Runner Note

The local environment did not have `pytest` installed.

Tests were executed manually by importing `tests/test_fund001.py` and running every function whose name starts with `test_`.

## Result

```text
manual_tests_passed = 6
```

## Verified Behaviors

1. FRED-style input columns are accepted.
2. Required output schema is produced.
3. Raw spread equals `DCPF3M - DTB3`.
4. 252-valid-observation normalization is calculated correctly.
5. Missing inputs are not forward-filled.
6. Repeated execution on identical input is deterministic.

## Pytest Status

`pytest` execution was attempted but could not run because the dependency is not installed in the active virtual environment.

This is an environment dependency limitation, not a failure of the FUND-001 implementation logic.

