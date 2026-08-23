# Verification Report

## Verified

- Input schema validation for factor columns.
- Monthly date normalization.
- Deterministic ticker ordering.
- Rolling 36-month OLS residualization.
- Minimum 24-observation guard.
- 12-1 residual aggregation.
- Residual volatility standardization.
- Percentile ranking bounds.
- State label generation.
- Frozen parameter guards.
- Missing factor rejection.
- Deterministic repeat execution.
- Python compile check.

## Synthetic Validation Output

```text
rows: 2160
valid_rows: 720
first_valid_month: 2019-01-31
last_valid_month: 2020-12-31
deterministic_hash: e2a6c762ab0ba7e910866ffd62b4e38d48023cde0d23b161fb3fbadc333d451d
monthly_returns_file_exists: False
factor_file_exists: False
repository_data_status: BLOCKED_EXTERNAL_DATA_REQUIRED
status: PASSED_SYNTHETIC_VERIFICATION
```

After data preparation, validator output changed to:

```text
monthly_returns_file_exists: True
factor_file_exists: True
repository_data_status: AVAILABLE
status: PASSED_SYNTHETIC_VERIFICATION
```

## Empirical Generation

Empirical construct state generation completed:

```text
rows: 96073
valid_rows: 66112
unique_tickers: 503
first_valid_month: 2014-02-28
last_valid_month: 2025-12-31
in_memory_deterministic_hash: ef4a622647d1931ff1fe8e34522fa2119cdca2d3f1d66381e6f073c7d3459ef7
persisted_artifact_hash: 217cc97a31084547845e2d970467e059ff8df0a161e7db6708950f89537e5bba
status: COMPLETE
```
