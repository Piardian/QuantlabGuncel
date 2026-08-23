# Measurement Approaches

## Spread-Based Measures

Spread measures capture tightness.

Examples:

- quoted bid-ask spread
- effective spread
- Roll implied spread
- high-low spread estimators

Strength:

- direct link to transaction cost

Limitation:

- true spreads require quote data; implied spreads depend on assumptions.

## Volume and Turnover Measures

Volume and turnover capture trading activity and rough capacity.

Examples:

- dollar volume
- share volume
- turnover ratio

Strength:

- easy to compute from daily data

Limitation:

- high volume does not always mean low trading cost or low price impact.

## Price-Impact Measures

Price-impact measures estimate how strongly trading or dollar volume moves prices.

Examples:

- Amihud illiquidity
- Kyle lambda
- Hasbrouck price impact

Strength:

- closer to market depth and execution cost

Limitation:

- some measures require intraday trades or strong modeling assumptions.

## Transaction-Cost Proxies

Examples:

- zero-return measure
- limited dependent variable transaction-cost estimates

Strength:

- useful when direct trading-cost data is unavailable

Limitation:

- may be more suitable for illiquid or infrequently traded markets.

## Order-Book Measures

Examples:

- quoted depth
- order-book imbalance
- depth across levels
- cancellation/replenishment behavior

Strength:

- direct view into depth and immediacy

Limitation:

- requires high-frequency order-book data.

## Aggregate Liquidity Measures

Examples:

- market-wide spread averages
- aggregate Amihud illiquidity
- Pastor-Stambaugh liquidity factor
- commonality in liquidity

Strength:

- can capture systematic liquidity state

Limitation:

- depends on panel construction and universe choice.

## Measurement Boundary

LR-001 does not choose the official LIQ-001 measurement. That decision belongs to CD-001.

