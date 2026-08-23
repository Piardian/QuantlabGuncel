# Alternative Definitions Review

## Bid-Ask Spread Liquidity

**Status:** Rejected for LIQ-001.

**Reason:** Strong theoretical and empirical support, but reliable quote data is not guaranteed in the current project. This would reduce reproducibility.

## Effective Spread

**Status:** Rejected for LIQ-001.

**Reason:** Requires trade and quote data. Better suited for a future high-frequency or execution-focused construct.

## Order-Book Depth

**Status:** Rejected for LIQ-001.

**Reason:** Directly measures depth but requires order-book data unavailable in the current daily-data pipeline.

## Roll Implied Spread

**Status:** Rejected for LIQ-001.

**Reason:** Can be computed from prices, but relies on assumptions about price reversals and may be unstable at daily frequency for broad panels.

## Volume / Dollar Volume Only

**Status:** Rejected for LIQ-001.

**Reason:** Easy to compute but incomplete. High volume does not necessarily imply low price impact or low trading cost.

## Pastor-Stambaugh Liquidity

**Status:** Deferred.

**Reason:** Theoretical support is strong, but the factor is more model-intensive and better suited to a later systematic liquidity-risk construct.

## Amihud-Style Aggregate Illiquidity

**Status:** Selected.

**Reason:** It has strong literature support, uses daily OHLCV data, is reproducible, and directly links absolute price movement to dollar trading volume.

