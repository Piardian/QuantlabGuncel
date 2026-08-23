# Executive Summary

VOL-001 / CD-001 freezes the official volatility construct for the V3.0 research program.

## Selected Construct

**US Equity Market Daily Yang-Zhang Volatility State**

## Measurement Family

Daily OHLC range-based realized volatility.

## Definition

VOL-001 uses SPY daily OHLC data to compute trailing 20-day Yang-Zhang realized volatility, annualized by 252 trading days.

The construct also includes:

- 252-day z-score
- 252-day percentile
- eligibility diagnostics

## What It Measures

VOL-001 measures current realized US equity market volatility state using overnight gap and intraday range information.

## What It Does Not Measure

- implied volatility
- GARCH conditional volatility
- high-frequency realized variance
- cross-sectional dispersion
- ATR
- alpha
- profitability
- directional return prediction

## Status

The VOL-001 construct is now frozen.

Next authorized stage:

`VOL-001 / IM-001`

