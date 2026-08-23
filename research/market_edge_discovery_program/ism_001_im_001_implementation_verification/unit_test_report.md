# Unit Test Report

## Standalone Validator

Command:

```powershell
.venv\Scripts\python.exe research\implementations\ism_001\validate_ism_001.py
```

Result:

```text
status: PASSED_SYNTHETIC_VERIFICATION
rows: 2352
valid_rows: 1764
unique_industries: 49
rank_monotonicity_violations: 0
repository_data_status: AVAILABLE
```

## Pytest Runner

Command attempted:

```powershell
.venv\Scripts\python.exe -m pytest research\implementations\ism_001\tests\test_ism001.py -q
```

Result:

```text
No module named pytest
```

Pytest is not installed in the current virtual environment. The standalone deterministic validator passed and the test file has been added for environments where pytest is available.
