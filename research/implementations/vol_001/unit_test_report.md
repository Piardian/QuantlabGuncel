# Unit Test Report

## Test Execution

Synthetic tests were executed directly with the project virtual environment.

```powershell
.venv\Scripts\python.exe -
```

## Test Results

| Test | Result |
| --- | --- |
| `test_feature_pipeline_follows_cd001_return_formula` | PASS |
| `test_model_builds_required_columns` | PASS |
| `test_model_is_deterministic_on_identical_input` | PASS |

## Coverage

The tests verify:

- overnight return formula
- open-to-close return formula
- Rogers-Satchell component formula
- output schema
- presence of Yang-Zhang volatility output
- presence of z-score output
- deterministic model execution on identical synthetic input

## Limitation

`pytest` was not required for this validation run. Test functions were invoked directly because prior project validation used the same approach when pytest was unavailable.

