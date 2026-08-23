# Construct Assumptions

## Core Assumptions

- Absolute price movement per unit of dollar volume is a reasonable daily proxy for price impact and illiquidity.
- The cross-sectional median across a fixed US equity universe represents aggregate market illiquidity more robustly than a mean.
- A 20-day rolling average captures persistent liquidity conditions better than a one-day raw value.
- A 252-day z-score makes the construct comparable across market periods by expressing liquidity stress relative to recent history.
- Daily OHLCV data is sufficient for this first reproducible liquidity construct, even though it cannot capture all liquidity dimensions.

## Market Assumptions

- The fixed equity universe is broad enough to represent US equity liquidity conditions.
- Volume and close data are reliable enough for daily price-impact proxies.
- Median aggregation reduces the influence of data errors and extreme single-security events.

## Interpretation Assumptions

- Higher values represent worse liquidity conditions.
- Lower values represent better liquidity conditions.
- LIQ-001 is a liquidity stress measure, not a complete market microstructure model.

## Non-Assumptions

LIQ-001 does not assume:

- liquidity predicts returns
- liquidity creates alpha
- daily proxies equal true execution cost
- Amihud-style illiquidity captures spread, depth, immediacy, and resiliency simultaneously

