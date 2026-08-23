# ISM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether implemented ISM-001 behaves as an internally coherent, reproducible and stable implementation of the frozen CD-001 construct.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown, portfolio construction or economic value were evaluated.

## Frozen Construct

ISM-001 is the **Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank**.

It computes compounded value-weighted industry returns from `t-12` through `t-2`, ranks all valid Ken French 49 industry portfolios cross-sectionally by month, and assigns percentile-based state labels.

## Data Scope

- State file: `output/ism_001/ism001_industry_momentum_state.csv`
- Rows: 58,751
- Unique industries: 49
- Valid observations: 55,285
- Full sample months: 1926-07-31 to 2026-05-31
- Valid construct months: 1927-07-31 to 2026-05-31

## Validation Results

- Post-warmup full 49-industry coverage: FAILED
- Top decile rate: 0.1071
- Bottom decile rate: 0.1071
- Middle rate: 0.7857
- Score mean: 0.5000
- Score range: 0.0000 to 1.0000
- Rank consistency: PASSED
- Deterministic hash matches IM generation report: PASSED

## Final CV-001 Classification

**Partially supported**

The construct is internally coherent, deterministic and stable across the available Ken French 49 industry portfolio sample. This conclusion is limited to construct validation and does not imply predictive validity or economic value.
