# Implementation Requirements

IM-001 must faithfully implement CD-001 without changing the construct.

## Required Components

- Config file containing frozen parameters.
- Feature pipeline calculating 12-1 returns.
- Cross-sectional ranking implementation.
- Top-decile flag output.
- Missing-data handling.
- Deterministic output serialization.
- Validation script.
- Reproducibility report.

## Required Verification

- Parameter values match CD-001.
- Output columns match CD-001.
- Rank scores remain within `[0, 1]`.
- Top-decile flag equals `score >= 0.90`.
- Re-running on identical inputs produces identical outputs.

## Forbidden

- No parameter tuning.
- No alternate lookback testing.
- No return prediction.
- No backtest.
- No economic validation.
