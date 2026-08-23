# Construct Specification

## Construct ID

`VOL-001`

## Construct Name

US Equity Market Daily Yang-Zhang Volatility State

## Construct Family

Market Volatility

## Construct Class

Continuous market-level realized-volatility state construct.

## Market Proxy

`SPY`

## Measurement Family

Range-based realized volatility using the Yang-Zhang OHLC estimator.

## Primary Question Answered

```text
What is the current realized volatility state of the US equity market?
```

## Inputs

- SPY daily adjusted or normalized open
- SPY daily adjusted or normalized high
- SPY daily adjusted or normalized low
- SPY daily adjusted or normalized close

## Parameters

These parameters are frozen:

| Parameter | Value | Rationale |
| --- | ---: | --- |
| volatility window | 20 trading days | Approximate one trading month and common current-state horizon |
| annualization factor | 252 | Standard US trading-day annualization convention |
| normalization window | 252 trading days | Approximate one trading year for state normalization |
| market proxy | SPY | Liquid broad US equity market proxy |

## Core Output

```text
vol001_yz_volatility_20d
```

Annualized trailing 20-day Yang-Zhang realized volatility.

## State Outputs

```text
vol001_zscore
vol001_percentile
```

These normalize the current volatility level against the trailing 252-day history.

## Interpretation

Higher values indicate a higher realized market volatility state.

No directional, alpha, profitability, or trading-performance interpretation is permitted at CD-001.

