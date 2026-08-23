# Limitations

## Implementation Limitations

- LIQ-001 implements a daily Amihud-style aggregate illiquidity construct only.
- It does not measure bid-ask spread, order-book depth, immediacy, or resiliency.
- Yahoo Finance data can change over time, so raw input snapshots should be archived for formal validation stages.
- The IM-001 validation run used a capped 60-symbol universe for practical verification.
- One ticker, `BF.B`, failed due to Yahoo Finance data availability or ticker-format handling.

## Scientific Boundary

IM-001 does not evaluate:

- construct validity
- mechanism validity
- predictive information
- alpha
- profitability
- economic utility

Those questions belong to later stages.

