# EXB-001 Rebalance Calendar Specification

## Frozen Calendar Rule

Exploratory rebalance dates must be the last valid trading day of each calendar month according to the Alpaca trading calendar.

## Decision Timing

Signals are evaluated after the close of the rebalance date using information available through that close only.

## Execution Timing

The earliest allowed exploratory execution timestamp is the next trading session after the rebalance decision date.

## Holiday Rule

If a calendar month ends on a non-trading day, the rebalance decision date is the previous valid trading day.

## Restriction

The rebalance calendar may not be changed after observing EXB-002 exploratory results.
