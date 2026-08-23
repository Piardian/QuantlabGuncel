# FUND-001 / IM-001 Package

## Construct

US Financial Commercial Paper Funding Spread Stress

## Formula

```text
DCPF3M - DTB3
```

## Main Scripts

- `fund001_funding_stress_model.py`
- `feature_pipeline.py`
- `validate_fund_001.py`

## Tests

- `tests/test_fund001.py`

## Reports

Runtime verification writes reports to:

```text
output/fund_001_validation
```

## Boundary

Implementation only. No predictive, trading, alpha, or economic evaluation.

