# FUND-001 / LR-001

# Methodology Comparison

## Purpose

This document compares measurement methodologies used in the Funding Stress literature.

No implementation is selected in LR-001.

## Spread-Based Measures

Examples:

- LIBOR-OIS spread,
- TED spread,
- bank funding spreads,
- SOFR-related funding spreads,
- repo spreads.

Strengths:

- simple,
- historically common,
- interpretable as funding-cost stress.

Weaknesses:

- may mix liquidity and credit risk,
- LIBOR transition limits continuity,
- unsecured bank funding markets changed structurally,
- may not capture secured funding or dealer balance-sheet pressure.

Evidence status: Moderately supported.

## Composite Index Components

Examples:

- OFR Financial Stress Index funding category,
- Chicago Fed NFCI risk/credit/leverage components.

Strengths:

- institutionally maintained,
- broad coverage,
- public documentation,
- often robust across stress episodes.

Weaknesses:

- may mix multiple constructs,
- component-level data can be harder to isolate,
- methodology may change through time.

Evidence status: Moderately supported.

## Central-Bank Operation Measures

Examples:

- bidding behavior in open-market operations,
- central-bank liquidity facility usage.

Strengths:

- closely tied to direct demand for liquidity,
- theoretically clean in some contexts.

Weaknesses:

- jurisdiction-specific,
- may depend on policy design,
- may not apply cleanly to US equity decision support.

Evidence status: Limited to moderately supported.

## Balance-Sheet And Leverage Measures

Examples:

- broker-dealer leverage,
- intermediary balance-sheet growth,
- repo and reverse repo activity,
- dealer inventory constraints.

Strengths:

- directly tied to intermediary funding capacity,
- theoretically important.

Weaknesses:

- lower frequency,
- reporting delays,
- hard to convert into daily market-state sensor,
- may not be point-in-time clean without care.

Evidence status: Moderately supported.

## Collateral And Margin Measures

Examples:

- haircuts,
- margin requirements,
- collateral scarcity,
- repo specialness.

Strengths:

- close to the funding spiral mechanism.

Weaknesses:

- data availability is difficult,
- public daily histories can be limited,
- institutional terms may not be observable.

Evidence status: Strong theoretical support, limited public measurement.

## Latent Or Composite Models

Examples:

- principal component models,
- financial stress indexes,
- dynamic factor models,
- regime models.

Strengths:

- can summarize multiple observable stress dimensions,
- may improve stability.

Weaknesses:

- construct interpretability can weaken,
- risk of mixing funding stress with adjacent constructs,
- requires strict preregistration.

Evidence status: Moderately supported if definition remains transparent.

## Methodological Implication

For CD-001, the safest scientific path is a narrow construct definition with explicit limitations. A broad composite may be useful later, but only if each component and weighting rule is frozen in advance.

