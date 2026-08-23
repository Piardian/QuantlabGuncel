# Rebalance Policy

## Frequency

Monthly.

## Rebalance Signal Date

First available trading day of each calendar month.

## Entry Date

Next available trading day after the signal date.

## Exit Date

The trading day immediately before the next entry date.

If implementation uses next rebalance close instead, WPC-002 must document the exact deterministic rule and apply it identically to workflow and benchmark.

## No Overlapping Sleeves

Only one active monthly portfolio sleeve may exist at a time.

## No Rebalance Optimization

WPC-002 must not compare monthly against weekly, quarterly or any alternative frequency.
