# BRD-001 / HV-001: Robustness Analysis

## Purpose

Evaluate whether the explanatory relationships depend only on the most extreme BRD-001 observations.

## Trimmed Extreme Check

The lowest 1% and highest 1% BRD-001 raw observations were removed.

The LOW_BREADTH versus HIGH_BREADTH differences remained directionally consistent:

- SPY distance from SMA200 remained higher in HIGH_BREADTH.
- SPY realized volatility remained lower in HIGH_BREADTH.
- SPY drawdown from 52-week high remained shallower in HIGH_BREADTH.
- SPY-above-SMA200 frequency remained higher in HIGH_BREADTH.

## Classification

```text
Supported by evidence
```

## Boundary

This is explanatory robustness only.

It does not test predictive validity or economic value.

