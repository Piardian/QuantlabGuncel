# RSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether implemented RSM-001 behaves as an internally coherent, reproducible and stable implementation of the frozen CD-001 construct.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown or economic value were evaluated.

## Frozen Construct

RSM-001 is the Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank.

It computes monthly security excess returns, removes common FF3 exposure using rolling 36-month OLS, aggregates residuals from `t-12` through `t-2`, standardizes by 36-month residual volatility and ranks securities cross-sectionally.

## Data Scope

- State file: `output/rsm_001/rsm001_residual_momentum_state.csv`
- Rows: 96,073
- Unique tickers: 503
- Valid observations: 66,112
- Full sample months: 2010-02-28 to 2025-12-31
- Valid construct months: 2014-02-28 to 2025-12-31

## Validation Results

- Average coverage ratio: 0.6881
- Minimum post-warmup coverage ratio: 0.8390
- Top decile rate: 0.1010
- Bottom decile rate: 0.1010
- Percentile mean: 0.5000
- Percentile range: 0.0000 to 1.0000
- Rank consistency: PASSED
- Deterministic hash matches IM generation report: PASSED

## Final CV-001 Classification

**Partially supported**

The construct is reproducible and internally coherent under the available data panel. The classification is not stronger than Partially Supported because the equity universe is current-constituent based rather than survivorship-free historical membership.
