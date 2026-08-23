# RSM-001 / MI-001 Mechanism Identification

## Purpose

Characterize the observable behavior represented by the validated RSM-001 residual momentum states.

No future returns, alpha, trading performance, strategy backtest, Sharpe, CAGR, drawdown, predictive validation or economic value were evaluated.

## Study Population

- Valid construct months: 2014-02-28 to 2025-12-31
- Valid observations: 66,112
- Unique tickers: 493
- TOP_DECILE observations: 6,679
- BOTTOM_DECILE observations: 6,679

## Mechanism Summary

RSM-001 represents a **factor-residual relative strength state**: it identifies securities with high or low intermediate-horizon residual performance after removing common Fama-French 3-factor exposure and scaling by residual volatility.

## Supported By Evidence

- TOP_DECILE has strongly positive mean standardized residual momentum score: 5.0255.
- BOTTOM_DECILE has strongly negative mean standardized residual momentum score: -5.6545.
- MIDDLE is centered near the cross-sectional middle with mean percentile 0.5000.
- RSM percentile and raw 12-1 momentum percentile are related but not identical; median monthly Spearman agreement is 0.7504.
- State persistence exists but is rotating; TOP_DECILE one-month retention is 0.6788, and BOTTOM_DECILE one-month retention is 0.6831.

## Partially Supported

- RSM-001 appears to separate idiosyncratic/residual winner and loser states rather than simple raw price winners and losers. This is supported by the raw-vs-residual rank agreement analysis, but the analysis does not evaluate future outcomes.

## Not Evaluated

- Predictive power
- Future returns
- Alpha
- Strategy profitability
- Economic utility

## MI-001 Classification

RSM-001 is best characterized as a **factor-residual cross-sectional leadership / residual winner-loser state construct** under the frozen CD-001 definition.
