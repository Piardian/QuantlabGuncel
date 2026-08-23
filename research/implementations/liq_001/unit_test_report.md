# Unit Test Report

## Test Environment

`pytest` was not installed in the active virtual environment, so the test functions were executed directly with Python.

Command:

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from tests.test_liq001 import (
    test_security_features_follow_cd001_formula,
    test_aggregate_builds_required_columns,
    test_model_is_deterministic_on_identical_input,
)
for test in [
    test_security_features_follow_cd001_formula,
    test_aggregate_builds_required_columns,
    test_model_is_deterministic_on_identical_input,
]:
    test()
    print(f'{test.__name__}: PASS')
'@ | ..\..\..\.venv\Scripts\python.exe -
```

## Results

- `test_security_features_follow_cd001_formula`: PASS
- `test_aggregate_builds_required_columns`: PASS
- `test_model_is_deterministic_on_identical_input`: PASS

## Coverage

The tests verify:

- security-level CD-001 formula
- log return calculation
- dollar volume calculation
- eligibility flag
- security illiquidity
- aggregate required columns
- minimum eligible-security rule
- deterministic output on identical synthetic input

