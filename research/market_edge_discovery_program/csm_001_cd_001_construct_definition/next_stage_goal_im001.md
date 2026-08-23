# CSM-001 / IM-001 Implementation Development & Verification

## Purpose

Implement the frozen CSM-001 construct exactly as defined in CD-001.

## Required Implementation

- Load adjusted-close panel.
- Compute `return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1`.
- Apply eligibility rules.
- Rank eligible securities cross-sectionally by date.
- Compute percentile momentum score.
- Output top-decile flag.
- Serialize deterministic construct state.

## Required Verification

- Frozen parameters match CD-001.
- Output schema matches CD-001.
- Ranking is monotonic with `return_12_1`.
- Scores are bounded in `[0, 1]`.
- Top-decile flag equals `score >= 0.90`.
- Identical input produces identical output.

## Forbidden

- No empirical testing.
- No predictive validation.
- No backtest.
- No optimization.
- No strategy recommendation.
