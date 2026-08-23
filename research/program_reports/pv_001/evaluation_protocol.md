# Evaluation Protocol

## Study Design
- Objective: predictive validation of the identified trend-related construct.
- No backtests were run and no parameters were tuned.
- The study uses executed trades only, from the frozen production architecture.
- Analysis window: 2010-01-01 through 2026-01-01.
- OOS protocol: expanding-window, year-by-year walk-forward validation.
- Initial training requirement: at least 100 trades before a year can be evaluated.

## Construct Proxy
Primary score: COMPOSITE_TREND_PROXY
Components:
- ema50_slope
- ema200_slope
- distance_above_ema50
- distance_above_ema200
- rs20
- rs60
- rs120
- atr_percent (inverse smoothness contribution)
- daily_range_percent (inverse smoothness contribution)

Secondary sensitivity score: TREND_STRENGTH_PROXY (rs20/rs60/rs120 only).

## Outcomes
- Binary: R_multiple > 0
- Continuous: R_multiple

## Primary Predictive Metrics
- ROC-AUC
- Rank IC (Spearman)
- Top-decile vs bottom-decile mean R lift
- Calibration slope across quintiles
- Year-by-year stability of sign and magnitude

## Statistical Tests
- Cluster bootstrap confidence intervals by year
- Within-year permutation test for AUC and rank IC
- One-sided sign test on yearly IC direction

## Data Scope
- Trades analyzed: 21,655
- Symbols represented: 496
- Entry years represented: 2010 to 2025

This protocol is fixed and was not altered after inspecting outcomes.