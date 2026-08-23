# Decision Rationale

## Decision

Freeze CRD-001 as:

```text
US High-Yield Credit Spread Stress measured by BAMLH0A0HYM2.
```

## Rationale by Criterion

| Criterion | Assessment |
|---|---|
| Literature support | Strong support for credit spreads as credit stress observables |
| Theoretical clarity | Directly linked to compensation for below-investment-grade corporate credit risk |
| Operational simplicity | Single public input series |
| Public data availability | Available through FRED |
| Reproducibility | High, subject to source revisions |
| Measurement reliability | Strong enough for construct lifecycle testing |
| Independence | More distinct from prior equity volatility, breadth, correlation, and liquidity constructs than broad stress composites |

## Why Not a Composite?

A composite could capture a broader stress state, but it would mix multiple mechanisms. CRD-001 intentionally starts with one narrow, interpretable credit-market observable.

## Why Not Excess Bond Premium?

Excess bond premium is theoretically important, but it requires model-based decomposition. CRD-001 prioritizes deterministic implementation from a public source.

## Why Not Baa-Treasury?

Baa-Treasury has historical depth, but CRD-001 prioritizes modern high-yield stress sensitivity and direct speculative-grade credit-market interpretation.

## Decision Boundary

The selected definition is not chosen because it is expected to forecast markets or improve portfolios. Those questions are explicitly reserved for later lifecycle stages.

