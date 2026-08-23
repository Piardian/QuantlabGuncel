# Measurement Approaches

## Purpose

Summarize major volatility measurement families without selecting the final VOL-001 construct.

## Close-to-Close Realized Volatility

Formula family:

```text
rolling_std(log_returns)
```

Inputs:

- close prices
- lookback window

Advantages:

- simple
- transparent
- reproducible from daily data

Limitations:

- ignores intraday range
- sensitive to window choice
- cannot separate overnight and intraday variation

Evidence category:

**Strongly supported**

## High-Frequency Realized Volatility

Formula family:

```text
sum(intraday_return^2)
```

Inputs:

- intraday price observations

Advantages:

- theoretically close to realized variation under suitable conditions
- widely used in financial econometrics

Limitations:

- requires intraday data
- sensitive to sampling frequency
- affected by market microstructure noise

Evidence category:

**Strongly supported**

## Parkinson Estimator

Inputs:

- high
- low

Advantages:

- uses intraday high-low range
- more information than close-to-close under ideal assumptions

Limitations:

- assumes continuous trading and no jumps in basic form
- ignores open and close information

Evidence category:

**Strongly supported**

## Garman-Klass Estimator

Inputs:

- open
- high
- low
- close

Advantages:

- uses full OHLC information
- extends range-based measurement

Limitations:

- assumptions may be violated by drift and overnight jumps

Evidence category:

**Strongly supported**

## Rogers-Satchell Estimator

Inputs:

- open
- high
- low
- close

Advantages:

- designed to be robust to drift under its assumptions

Limitations:

- still relies on OHLC data quality and model assumptions

Evidence category:

**Strongly supported**

## Yang-Zhang Estimator

Inputs:

- open
- high
- low
- close

Advantages:

- accounts for opening jumps and drift independence in the published framework
- combines overnight and intraday components

Limitations:

- more complex
- requires careful implementation

Evidence category:

**Strongly supported**

## ATR-Derived Volatility

Inputs:

- high
- low
- previous close

Advantages:

- captures gaps and range
- common in practitioner risk sizing
- easy to normalize by price

Limitations:

- not a formal variance estimator
- less directly tied to econometric volatility literature

Evidence category:

**Moderately supported**

## ARCH/GARCH Conditional Volatility

Inputs:

- returns
- model specification

Advantages:

- models volatility clustering and conditional heteroskedasticity

Limitations:

- requires estimation choices
- deterministic reproducibility depends on model implementation and optimization settings

Evidence category:

**Strongly supported**

## Implied Volatility

Inputs:

- option prices
- interest rates
- expiration structure
- index methodology

Advantages:

- forward-looking
- market-priced

Limitations:

- includes volatility risk premium
- requires liquid options data
- may not be available for every asset or historical period

Evidence category:

**Strongly supported**

## Cross-Sectional Volatility

Inputs:

- returns across securities

Advantages:

- measures dispersion across market constituents

Limitations:

- different from time-series volatility of the market index

Evidence category:

**Moderately supported**

