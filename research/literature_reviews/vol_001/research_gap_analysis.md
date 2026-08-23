# Research Gap Analysis

## Core Gap for This Project

The project lacks a standalone volatility-state construct.

MR-001 includes volatility as part of a latent market-regime model. LIQ-001 measures liquidity stress. Neither directly answers:

```text
What is the current volatility state of the market?
```

## Literature-to-Project Gap

The literature offers many volatility definitions, but the project must choose one precise operational construct in CD-001.

## Candidate CD-001 Decision Axes

CD-001 should evaluate:

- daily data availability vs intraday or option-data requirement
- realized vs implied volatility
- time-series market volatility vs cross-sectional dispersion
- close-to-close simplicity vs OHLC information richness
- interpretability vs estimator complexity
- reproducibility and deterministic implementation
- alignment with "current market volatility state"

## Open Scientific Questions Before CD-001

- Should VOL-001 represent realized current volatility or expected future volatility?
- Should VOL-001 use only SPY or a broader market panel?
- Should VOL-001 prioritize OHLC estimators over close-to-close returns?
- Should volatility be normalized into a state score?
- Should the construct be a scalar level, percentile, z-score or state classification?

## Boundary

These questions are for construct definition, not for optimization.

No answer should be selected because it appears profitable.

