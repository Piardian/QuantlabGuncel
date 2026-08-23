# FUND-001 / LR-001

# Research Gap Analysis

## Gap 1: Post-LIBOR Funding Stress Measurement

The transition away from LIBOR creates a major measurement problem. Many historical stress proxies were built around LIBOR-based spreads, but modern funding markets increasingly require alternative reference-rate based measures.

CD-001 must decide whether to use a legacy proxy, a modern proxy, or a documented bridge.

## Gap 2: Funding Stress vs Credit Stress

Funding spreads often contain both liquidity and credit premia. The literature recognizes this issue, but clean separation is difficult.

This is especially important because CRD-001 already exists as a separate Credit Stress construct.

## Gap 3: Public Daily Measurement

Many direct funding mechanisms are not observable in public daily data. This includes haircuts, margin terms, and institution-specific funding conditions.

## Gap 4: Secured vs Unsecured Funding

Unsecured bank funding, repo funding, and collateral funding are related but not identical. A single construct may not represent all three.

## Gap 5: Composite vs Narrow Construct

Composite indexes are convenient and institutionally recognized, but can blur construct identity. Narrow spread-based proxies are interpretable but may be incomplete.

CD-001 must balance interpretability against coverage.

## Gap 6: Independence From Existing Constructs

FUND-001 must be evaluated as distinct from:

- LIQ-001,
- VOL-001,
- CRD-001,
- COR-001,
- BRD-001,
- MR-001.

This cannot be fully resolved in LR-001, but it should guide CD-001 and later validation.

## Gap 7: Decision Domain

The literature supports funding stress as important, but does not imply a single intended decision domain.

Possible future domains include:

- systemic risk monitoring,
- risk-budget adjustment,
- leverage control,
- liquidity reserve decisions,
- portfolio stress awareness.

These are not evaluated in LR-001.

