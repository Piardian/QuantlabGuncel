# Decision Rationale

## Selected Construct

US Equity Market Average Pairwise Correlation State

## Why This Definition Was Selected

The selected definition is:

- directly aligned with market correlation literature
- simple enough for deterministic implementation
- reproducible from daily price data
- interpretable as broad market co-movement
- distinct from volatility, liquidity, breadth, and market regime
- suitable for later construct validation

## Why Average Pairwise Correlation

Average pairwise correlation directly asks whether securities are moving together.

This is the cleanest first operationalization of a market-correlation state because it avoids mixing correlation with option-implied expectations, tail dependence, systemic factor concentration, or cross-asset allocation.

## Why 60 Trading Days

The 60-day window approximates one calendar quarter of daily observations. It provides more stability than a very short window while remaining more responsive than a one-year estimate.

This is a construct-definition decision, not a performance optimization.

## Why 252-Day Normalization

The 252-day normalization window provides one approximate trading year of context for whether current correlation is unusually high or low relative to recent history.

This is a state-normalization convention, not a threshold rule.

## Why Not DCC Or Implied Correlation

DCC and implied correlation are scientifically important but introduce additional modeling or data dependencies. COR-001 is intended to be the simplest reproducible realized-correlation state construct.

## Why Not PCA Concentration

PCA concentration is related to systemic risk and common-factor dominance, but it is not identical to average pairwise co-movement. Selecting average pairwise correlation keeps COR-001 focused on a direct correlation construct.

## Final Decision

Freeze COR-001 as:

```text
US Equity Market Average Pairwise Correlation State
```

Proceed to IM-001 after human approval.

