# Construct Specification

## Construct Name

**US Equity Aggregate Daily Illiquidity**

## Construct ID

`LIQ-001`

## Construct Type

Continuous market-level liquidity stress construct.

## Theoretical Family

Daily price-impact / illiquidity proxy.

## Literature Anchor

The selected construct is anchored in the Amihud illiquidity family:

```text
absolute return / dollar volume
```

This family is widely used when direct bid-ask, quote, trade, or order-book data is unavailable.

## Market Scope

US equities.

## Frequency

Daily.

## Inputs

For every security in the fixed research universe:

- daily close
- daily volume

## Required Derived Variables

- daily log return
- daily dollar volume
- security-level Amihud-style illiquidity
- cross-sectional median illiquidity
- 20-day smoothed illiquidity
- 252-day rolling z-score

## Mathematical Specification

```text
log_return_i,t = ln(close_i,t / close_i,t-1)
dollar_volume_i,t = close_i,t * volume_i,t
illiquidity_i,t = abs(log_return_i,t) / dollar_volume_i,t
aggregate_illiquidity_t = median_i(illiquidity_i,t)
liq001_illiquidity_20d_t = mean(aggregate_illiquidity_t over trailing 20 trading days)
liq001_zscore_t = zscore(liq001_illiquidity_20d_t over trailing 252 trading days)
```

## Output Interpretation

Higher `liq001_zscore` means worse aggregate liquidity conditions relative to the trailing one-year history.

Lower `liq001_zscore` means better aggregate liquidity conditions relative to the trailing one-year history.

## Data Coverage Rule

The daily aggregate is valid only if at least 50 eligible securities are available.

## Frozen Status

All formulas, windows, inputs, and eligibility rules in this document are frozen after CD-001.

