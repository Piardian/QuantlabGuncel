# BRD-001 / CD-001: Decision Rationale

## Selected Construct

US Equity 200-Day Moving-Average Breadth State.

## Why This Definition Was Selected

The selected definition provides the clearest balance of:

- literature support
- theoretical clarity
- operational simplicity
- reproducibility
- data availability
- measurement reliability

## Scientific Rationale

The construct directly measures how many securities participate in a long-term positive trend state.

This aligns with the market-breadth idea that index-level market movement should be interpreted alongside internal participation.

## Operational Rationale

The selected construct requires only adjusted close data.

This reduces dependency on volume quality, sector classification quality, intraday data, or historical constituent metadata.

## Reproducibility Rationale

The formula is deterministic:

```text
close_i,t > SMA200_i,t
```

The market-level value is a simple percentage across eligible securities.

Two independent researchers using the same data and universe should obtain the same result.

## Why Not Advance / Decline Breadth

Daily A/D measures are direct but noisy.

They may be better suited for a short-term participation construct rather than the first stable BRD-001 state construct.

## Why Not Volume Breadth

Volume breadth is meaningful but creates additional data-quality and concentration concerns.

## Why Not New High / New Low Breadth

New high/new low breadth captures extreme participation but can be sparse and lookback-dependent.

## Why Not Sector Breadth

Sector breadth is valuable but requires a reliable sector taxonomy.

That introduces another construct layer.

## Decision Boundary

This decision does not imply the selected definition is more predictive, more profitable, or economically superior.

It only means this definition is the most appropriate first BRD-001 construct under CD-001 decision criteria.

