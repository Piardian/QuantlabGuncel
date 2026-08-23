# Decision Rationale

## Selected Definition

LIQ-001 is defined as **US Equity Aggregate Daily Illiquidity** based on an Amihud-style daily price-impact proxy.

## Why This Definition Was Selected

This definition offers the best balance of:

1. Literature support
2. Theoretical clarity
3. Data availability
4. Reproducibility
5. Operational simplicity
6. Measurement reliability

## Scientific Rationale

Amihud-style illiquidity is one of the most established daily-data liquidity proxies.
It connects price movement to dollar trading volume, making it a practical proxy for price impact and trading friction.

## Project Fit

The current project can reliably obtain daily close and volume data. Therefore a daily OHLCV-compatible measure is the most reproducible starting point.

## Why Not a Richer Liquidity Construct?

Bid-ask spread, effective spread, depth, and resiliency are scientifically important but require data the project does not reliably possess.

CD-001 prioritizes a construct that two independent researchers can reproduce from the existing data pipeline.

## Decision Boundary

Expected predictive performance, alpha, profitability, or economic utility were not considered.

