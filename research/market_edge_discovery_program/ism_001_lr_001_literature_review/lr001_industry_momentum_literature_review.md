# ISM-001 / LR-001 Industry Momentum Literature Review

## Purpose

Synthesize the scientific literature surrounding Industry Momentum as an edge-mechanism construct.

This stage does not freeze a construct, select an industry taxonomy, choose lookback windows, implement code, run backtests, optimize, claim alpha, or recommend production use.

## Primary Research Question

What does the current scientific literature collectively conclude about Industry Momentum as an independent expected-return mechanism?

## Executive Finding

Industry Momentum is a recognized and scientifically important momentum-family construct.

The literature supports the idea that industry-level return persistence is empirically relevant, but the interpretation is not settled. Some evidence suggests industry components explain a meaningful part of individual-stock momentum, while other research argues that stock-specific momentum, risk dynamics, or autocorrelation structures remain important.

Final LR-001 classification:

**Moderate-High literature support with material implementation and interpretation risks**

## Canonical Literature Anchor

The central paper is Moskowitz and Grinblatt's "Do Industries Explain Momentum?", which documents a strong industry component in momentum and argues that industry momentum accounts for much of individual stock momentum.

This makes ISM-001 scientifically distinct from:

- CSM-001: individual stock cross-sectional momentum.
- TSM-001: own-security time-series momentum state.
- RSM-001: factor-residual individual momentum.

## Main Theoretical Mechanisms

### 1. Industry-Level Information Diffusion

Information may diffuse slowly across firms in the same or related industries. This supports the possibility that industry-level winners continue to lead because investors update related firms gradually.

### 2. Industry Common Component Persistence

If industry return components are persistent, then stocks inside winning industries may inherit part of that persistence.

### 3. Lead-Lag Effects

Large firms, liquid firms, or economically central industries may incorporate information first, with related firms or industries responding later.

### 4. Behavioral Underreaction

Investors may underreact to industry-wide news, producing delayed adjustment at the group level.

### 5. Risk-Based / Macro Variation

Some momentum literature links momentum payoffs to time-varying expected returns, macroeconomic conditions, or common risk exposures. This remains a competing explanation.

## Empirical Evidence Summary

Supported by literature:

- Industry momentum exists as a documented empirical pattern in foundational U.S. equity studies.
- Industry components can explain a substantial portion of raw individual-stock momentum in some samples.
- Industry information diffusion and lead-lag behavior are plausible and studied mechanisms.
- Industry momentum is sufficiently distinct to justify separate construct research.

Conflicting or limited evidence:

- The claim that industry momentum is the primary source of all individual momentum is contested.
- Some evidence favors stock-specific momentum or residual momentum explanations.
- Results can depend on formation/holding horizon, skip-month convention, industry taxonomy, sample period and weighting.
- Replication strength is less broad than canonical cross-sectional momentum.

## Measurement Families

LR-001 identifies several measurement families, but does not select among them:

1. Industry portfolio momentum.
2. Stock signal based on parent-industry momentum.
3. Industry-adjusted stock momentum.
4. Lead-lag industry momentum.
5. Sector-level coarse momentum.
6. Text-based or peer-based industry momentum.

CD-001 must freeze exactly one operational definition.

## Key Methodological Risks

- Industry taxonomy discretion.
- Point-in-time classification availability.
- Current industry classification look-ahead risk.
- Survivorship bias in universe membership.
- Equal-weighted versus value-weighted industry returns.
- Thin industry handling.
- Industry mergers, classification changes and ticker history.
- Overgeneralizing long-short academic results to long-only or stock-selection settings.

## Interpretation Boundary

LR-001 supports proceeding to construct definition.

It does not support:

- Predictive validity in this repository.
- Economic value.
- Production deployment.
- Any claim that ISM is superior to CSM, TSM or RSM.

## Conclusion

Industry Momentum should proceed to CD-001.

CD-001 must be strict: the industry taxonomy, membership policy, weighting scheme, formation window, state output and missing-data rules must be frozen before any implementation or empirical validation.

