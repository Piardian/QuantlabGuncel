# BRD-001 / FSR-001: Evidence Summary

## RP-001

Market Breadth received a GO decision.

It was judged scientifically relevant, distinct from volatility, liquidity, market regime and momentum, and sufficiently measurable for a dedicated research program.

## LR-001

The literature review found Market Breadth to be a recognized market-internals construct.

Support was moderate to strong, with especially strong practitioner adoption.

## CD-001

The construct was frozen as:

```text
US Equity 200-Day Moving-Average Breadth State
```

Primary value:

```text
brd001_pct_above_sma200
```

## IM-001

The construct was implemented deterministically and verified with synthetic data.

Verification result:

```text
Successfully implemented
```

## CV-001

Construct validation was supported.

BRD-001 produced bounded, interpretable and non-degenerate breadth values with sufficient coverage.

## MI-001

Mechanism identification was supported.

BRD-001 primarily represents long-term cross-sectional trend participation and internal market confirmation.

## HV-001

Hypothesis validation was supported.

The explanatory mechanism was statistically validated using same-day and trailing observable variables.

## PV-001

Predictive validation was partially supported.

Supported:

- future realized volatility
- future trend deterioration risk

Partially supported:

- future drawdown risk

Not supported:

- future returns

## EV-001

Economic validation was supported for predefined risk-management workflows.

Supported:

- risk budgeting
- volatility targeting
- trend deterioration risk control

Partially supported:

- portfolio risk control versus buy-and-hold

## CC-001

BRD-001 was classified as:

```text
Market Breadth / Risk Management Construct
```

