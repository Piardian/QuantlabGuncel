# Executive Summary

BRD-001 / CD-001 defines the official Market Breadth construct.

## Selected Construct

**US Equity 200-Day Moving-Average Breadth State**

## Definition

BRD-001 measures the percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above their own 200-day simple moving average.

## Primary Output

```text
brd001_pct_above_sma200
```

## Interpretation

Higher values indicate broader participation above long-term trend.

Lower values indicate narrower participation or broad deterioration below long-term trend.

## Why This Construct Was Selected

It is literature-supported, simple, deterministic, close-only, broadly used in practitioner market-internals analysis, and reproducible from daily panel data.

## Major Limitation

The universe is a fixed current-constituent universe, not survivorship-free historical constituents.

This limitation must be carried forward.

## Final Status

The BRD-001 construct is now frozen.

Any change requires restarting from CD-001.

## Boundary

CD-001 makes no predictive, economic, profitability, alpha, or production-suitability claim.

