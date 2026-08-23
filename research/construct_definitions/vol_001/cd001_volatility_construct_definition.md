# VOL-001 / CD-001: Volatility Construct Definition

## Purpose

Define the exact Market Volatility construct that will be investigated throughout the remaining V3.0 lifecycle.

This stage freezes the construct. It does not test prediction, profitability, alpha, or economic utility.

## Selected Construct

**US Equity Market Daily Yang-Zhang Volatility State**

## Construct Type

Continuous market-level volatility-state construct.

## Definition

VOL-001 measures the current volatility state of the US equity market using SPY daily OHLC data and a trailing Yang-Zhang realized volatility estimator.

The construct is designed to represent realized market volatility state, including overnight gap variation and intraday range variation.

## Market Proxy

The US equity market is represented by:

```text
SPY
```

SPY is used as a liquid, reproducible daily OHLC proxy for broad US equity market exposure.

## Required Inputs

For each trading day `t`:

- adjusted or normalized open
- adjusted or normalized high
- adjusted or normalized low
- adjusted or normalized close

All four OHLC fields must be mutually adjusted on the same basis.

## Core Returns

For day `t`:

```text
overnight_return_t = ln(open_t / close_t-1)
open_to_close_return_t = ln(close_t / open_t)
high_open_return_t = ln(high_t / open_t)
high_close_return_t = ln(high_t / close_t)
low_open_return_t = ln(low_t / open_t)
low_close_return_t = ln(low_t / close_t)
```

## Rogers-Satchell Component

```text
rs_t =
    high_open_return_t * high_close_return_t
    + low_open_return_t * low_close_return_t
```

## Yang-Zhang Rolling Variance

Using a trailing window of:

```text
vol_window = 20 trading days
```

For each day `t`, compute over the trailing 20 observations ending at `t`:

```text
sigma_o2_t = sample_variance(overnight_return)
sigma_c2_t = sample_variance(open_to_close_return)
sigma_rs_t = mean(rs)
```

The Yang-Zhang weighting constant is:

```text
k = 0.34 / (1.34 + (vol_window + 1) / (vol_window - 1))
```

The daily Yang-Zhang variance estimate is:

```text
yz_variance_t =
    sigma_o2_t
    + k * sigma_c2_t
    + (1 - k) * sigma_rs_t
```

Annualized volatility is:

```text
vol001_yz_volatility_20d_t = sqrt(max(yz_variance_t, 0) * 252)
```

## Normalized Volatility State

The normalized volatility-state score is:

```text
vol001_zscore_t =
    (vol001_yz_volatility_20d_t - rolling_mean(vol001_yz_volatility_20d_t, 252))
    / rolling_std(vol001_yz_volatility_20d_t, 252)
```

The percentile state is:

```text
vol001_percentile_t =
    count(values <= vol001_yz_volatility_20d_t within trailing 252 valid values)
    / 252
```

The rolling 252-day window includes the current day and requires 252 valid `vol001_yz_volatility_20d` observations.

## Outputs

Each trading day receives:

- `vol001_yz_variance_20d`
- `vol001_yz_volatility_20d`
- `vol001_zscore`
- `vol001_percentile`
- `vol001_valid_observation`

Higher values indicate a higher realized volatility state.

## Eligibility Rules

A day is eligible for raw return calculation if:

- current open, high, low, and close are positive
- previous close is positive
- high is greater than or equal to both open and close
- low is less than or equal to both open and close
- all required log returns are finite

A day is eligible for `vol001_yz_volatility_20d` only when 20 valid raw observations are available in the trailing window.

A day is eligible for `vol001_zscore` and `vol001_percentile` only when 252 valid volatility observations are available in the trailing normalization window.

## Primary Volatility Dimension

VOL-001 primarily represents:

- realized market volatility
- daily OHLC range variation
- overnight gap variation
- normalized volatility state

## Non-Goals

VOL-001 does not attempt to:

- measure implied volatility
- model option-market expectations
- estimate GARCH conditional variance
- measure intraday high-frequency realized variance
- measure cross-sectional dispersion
- forecast returns
- maximize trading performance
- produce buy/sell signals
- optimize thresholds

## Final CD-001 Status

The VOL-001 construct is now frozen.

Any future change to proxy, variables, formula, rolling window, normalization window, eligibility rules, or outputs requires restarting from CD-001.
