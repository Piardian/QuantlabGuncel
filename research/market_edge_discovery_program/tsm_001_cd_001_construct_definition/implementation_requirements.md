# Implementation Requirements

IM-001 must faithfully implement CD-001 without changing the construct.

## Required Components

- Config file containing frozen parameters.
- Feature pipeline calculating raw 12-1 own returns.
- Direction-score assignment.
- State-label assignment.
- Missing-data handling.
- Deterministic output serialization.
- Validation script.
- Reproducibility report.

## Required Verification

- Parameter values match CD-001.
- Output columns match CD-001.
- Positive prior return maps to `+1` and `POSITIVE`.
- Negative prior return maps to `-1` and `NEGATIVE`.
- Zero prior return maps to `0` and `NEUTRAL`.
- Re-running on identical input produces identical output.

## Forbidden

- No volatility scaling.
- No cross-sectional ranking.
- No return prediction.
- No backtest.
- No economic validation.
