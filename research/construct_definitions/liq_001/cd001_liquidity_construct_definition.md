# LIQ-001 / CD-001: Liquidity Construct Definition

## Purpose

Define the exact Market Liquidity construct that will be investigated throughout the remaining V3.0 lifecycle.

This stage freezes the construct. It does not test prediction, profitability, alpha, or economic utility.

## Selected Construct

**US Equity Aggregate Daily Illiquidity**

## Construct Type

Continuous market-level liquidity stress construct.

## Definition

LIQ-001 measures aggregate US equity market illiquidity using a daily Amihud-style price-impact proxy computed across a fixed US equity universe.

For each security `i` on day `t`:

```text
illiquidity_i,t = abs(log_return_i,t) / dollar_volume_i,t
```

where:

```text
log_return_i,t = ln(close_i,t / close_i,t-1)
dollar_volume_i,t = close_i,t * volume_i,t
```

The market-level daily illiquidity value is:

```text
aggregate_illiquidity_t = median(illiquidity_i,t across eligible securities)
```

The smoothed construct value is:

```text
liq001_illiquidity_20d_t = rolling_mean(aggregate_illiquidity_t, 20 trading days)
```

The normalized liquidity stress score is:

```text
liq001_zscore_t =
    (liq001_illiquidity_20d_t - rolling_mean(liq001_illiquidity_20d_t, 252))
    / rolling_std(liq001_illiquidity_20d_t, 252)
```

Higher values indicate worse aggregate liquidity conditions.

## Primary Liquidity Dimension

LIQ-001 primarily represents:

- price impact
- aggregate market illiquidity
- market trading friction

It does not directly measure quoted spread, order-book depth, immediacy, or resiliency.

## Inputs

- Daily close
- Daily volume
- Fixed US equity universe

## Outputs

Each trading day receives:

- `aggregate_illiquidity`
- `liq001_illiquidity_20d`
- `liq001_zscore`
- coverage diagnostics

## Eligibility Rules

A security-day is eligible if:

- close is positive
- volume is positive
- previous close is available
- dollar volume is positive
- log return can be computed

The aggregate value is computed only when at least 50 eligible securities are available on that date.

## Non-Goals

LIQ-001 does not attempt to:

- measure quoted spread
- measure order-book depth
- estimate execution cost directly
- model intraday liquidity
- forecast returns
- maximize trading performance
- optimize thresholds
- produce buy/sell signals

## Final CD-001 Status

The LIQ-001 construct is now frozen.

Any future change to variables, formula, smoothing window, normalization window, eligibility rules, or outputs requires restarting from CD-001.

