# FUND-001 / CD-001

# Decision Rationale

## Decision

Select:

```text
US Financial Commercial Paper Funding Spread Stress
```

using:

```text
DCPF3M - DTB3
```

## Why This Definition Best Fits FUND-001

The literature supports Funding Stress as a financing-capacity construct. The selected spread directly compares private short-term financial funding costs with short-term Treasury bill rates.

This makes the construct:

- narrow,
- interpretable,
- public,
- reproducible,
- daily-frequency in source design,
- less exposed to LIBOR discontinuation than LIBOR-OIS or TED,
- distinct from previously completed constructs.

## Why Not A Broader Composite

A broad composite could capture more funding-stress dimensions, but it would blur construct identity.

At CD-001, scientific clarity is more important than coverage.

## Why Not Repo Or Haircuts

Repo and haircut measures are theoretically strong, but public daily histories and standardized implementation rules are more difficult. Selecting them now would introduce measurement fragility.

## Why Not Institution-Level Balance Sheets

Dealer balance-sheet measures are relevant but lower-frequency and potentially lagged. This is less suitable for a market-state sensor intended to be reproducible from public time series.

## Why Not LIBOR-Based Measures

LIBOR-based measures are historically important, but modern reproducibility and interpretation are weakened by the LIBOR transition and changes in unsecured bank funding markets.

## Scientific Boundary

This decision is not a claim that the selected spread is predictive, profitable, economically useful, or superior to alternatives. It is only a construct-definition decision.

