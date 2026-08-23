# Executive Summary

LIQ-001 / CD-001 freezes the official liquidity construct for the V3.0 research program.

## Selected Construct

**US Equity Aggregate Daily Illiquidity**

## Measurement Family

Amihud-style daily price-impact / illiquidity proxy.

## Definition

For each security:

```text
illiquidity = abs(daily log return) / dollar volume
```

For the market:

```text
aggregate illiquidity = cross-sectional median security illiquidity
```

The construct also includes:

- 20-day smoothed aggregate illiquidity
- 252-day normalized z-score
- coverage diagnostics

## Why Selected

This construct is literature-supported, reproducible from daily OHLCV data, operationally simple, and theoretically aligned with price-impact liquidity.

## What It Measures

Aggregate daily liquidity stress in US equities.

## What It Does Not Measure

- quoted spread
- order-book depth
- intraday immediacy
- resiliency
- direct execution cost
- alpha
- profitability

## Status

The LIQ-001 construct is now frozen.

Next authorized stage:

`LIQ-001 / IM-001`

