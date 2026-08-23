# TSM-001 / PV-001 Predictive Validation

## Purpose

Evaluate whether the validated TSM-001 raw 12-1 time-series momentum construct contains statistical predictive information about predefined future own-asset outcomes.

This is predictive validation only. It is not a trading strategy backtest, not economic validation, and not a production recommendation.

## Preregistered Forecast Horizons

- 21 trading days
- 63 trading days
- 126 trading days

## Preregistered Outcomes

- Future own-asset adjusted-close return
- Future own-asset realized volatility
- Future own-asset max drawdown over the horizon

## Evidence Base

- Source state file: `output/tsm_001_cv001/tsm001_construct_state.csv`
- Observations: 1,768,840
- Unique tickers: 499
- Date range: 2011-01-03 to 2025-12-30

## Results By Horizon

- 21d: return Not supported, volatility Supported by evidence, drawdown Supported by evidence; return diff -0.005747, vol diff -0.061265, drawdown diff 0.008253
- 63d: return Not supported, volatility Supported by evidence, drawdown Supported by evidence; return diff -0.015048, vol diff -0.050999, drawdown diff 0.010243
- 126d: return Not supported, volatility Supported by evidence, drawdown Supported by evidence; return diff -0.023867, vol diff -0.044840, drawdown diff 0.011849

## Overall PV-001 Classification

**Partially supported**

The conclusion is limited to statistical predictive information in the evaluated current-constituent universe and predefined horizons. No economic utility, portfolio value, alpha or trading profitability is inferred.
