# TSM-001 / IM-001 Implementation Development & Verification

## Purpose

Implement the frozen TSM-001 construct exactly as defined in CD-001.

## Required Implementation

- Load adjusted-close panel.
- Compute `tsm_return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1`.
- Apply eligibility rules.
- Compute direction score.
- Assign POSITIVE / NEGATIVE / NEUTRAL state.
- Serialize deterministic construct state.

## Required Verification

- Frozen parameters match CD-001.
- Output schema matches CD-001.
- State assignment is correct for positive, negative and zero returns.
- Non-positive or missing prices produce invalid observations.
- Identical input produces identical output.

## Forbidden

- No empirical testing.
- No predictive validation.
- No volatility scaling.
- No backtest.
- No economic validation.
- No production recommendation.
