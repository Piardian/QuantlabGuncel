# BRD-001 / MI-001: Breadth State Profile

## Purpose

Profile observable market characteristics across BRD-001 breadth states.

## State Definitions

The states are descriptive quintile-style buckets:

| State | Definition | Observations |
| --- | --- | ---: |
| LOW_BREADTH | Bottom 20% of valid BRD-001 values | 766 |
| MID_BREADTH | Middle 60% of valid BRD-001 values | 2,293 |
| HIGH_BREADTH | Top 20% of valid BRD-001 values | 765 |

These states are not production thresholds.

## State Profile

| State | Avg Breadth | SPY Above SMA200 | SPY Dist SMA200 | SPY 20d Vol | SPY 52w DD |
| --- | ---: | ---: | ---: | ---: | ---: |
| HIGH_BREADTH | 0.8708 | 100.00% | 0.1012 | 0.1078 | -0.0068 |
| MID_BREADTH | 0.6978 | 98.04% | 0.0589 | 0.1202 | -0.0242 |
| LOW_BREADTH | 0.3647 | 20.50% | -0.0411 | 0.2607 | -0.1137 |

## Interpretation

HIGH_BREADTH describes broad long-term trend participation.

LOW_BREADTH describes narrow or deteriorated long-term participation and stress-like contemporaneous market conditions.

Classification:

```text
Supported by evidence
```

## Boundary

This profile describes same-day and trailing market characteristics.

It does not evaluate future outcomes.

