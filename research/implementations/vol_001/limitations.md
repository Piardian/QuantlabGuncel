# Limitations

## Implementation Scope

This implementation covers only the frozen CD-001 construct:

**US Equity Market Daily Yang-Zhang Volatility State**

## Excluded Volatility Families

The implementation does not include:

- implied volatility
- VIX
- GARCH conditional volatility
- high-frequency realized variance
- ATR
- cross-sectional dispersion

## Data Source Limitation

Validation used Yahoo Finance data. Yahoo data can be revised, and live redownloads may not produce byte-identical snapshots.

## Input Snapshot Requirement

Scientific reproducibility requires archiving the input OHLC snapshot used for validation.

## No Predictive or Economic Claim

IM-001 does not evaluate whether VOL-001 predicts future volatility, drawdown, returns, or economic outcomes.

## No Alpha Claim

VOL-001 is not implemented as a trading signal.

