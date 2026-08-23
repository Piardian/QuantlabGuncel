# Construct Limitations

## 1. Not Implied Volatility

VOL-001 does not measure option-implied expected future volatility.

## 2. Not High-Frequency Realized Variance

VOL-001 uses daily OHLC data and does not incorporate intraday sampling.

## 3. Not Conditional Model Volatility

VOL-001 does not estimate ARCH, GARCH, stochastic volatility or other parametric conditional volatility models.

## 4. Not Cross-Sectional Dispersion

VOL-001 measures SPY time-series volatility, not dispersion across individual securities.

## 5. Proxy Dependence

The construct depends on SPY as the market proxy. It may differ from volatility measured on SPX, total-market ETFs or equal-weighted market baskets.

## 6. Window Dependence

The 20-day and 252-day windows are fixed operational conventions. They are not optimized and may not be ideal for every research question.

## 7. OHLC Data Quality

The construct requires internally consistent adjusted or normalized OHLC data. Vendor adjustment issues can affect results.

## 8. No Predictive or Economic Claim

CD-001 does not establish that VOL-001 predicts future risk or improves portfolio decisions.

## 9. No Alpha Claim

VOL-001 is not a standalone trading signal or return predictor.

