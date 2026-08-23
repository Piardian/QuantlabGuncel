# PEAD-001 / LR-001 Literature Review

## Purpose

Synthesize the scientific literature on Post-Earnings Announcement Drift (PEAD) as an event-driven expected-return mechanism.

This review does not define the frozen PEAD-001 construct, implement indicators, run tests, backtest, optimize, or claim alpha.

## Primary Research Question

What does the current scientific literature collectively conclude about PEAD as an independent expected-return mechanism?

## High-Level Finding

PEAD is one of the most established accounting and finance anomalies. The literature generally defines it as the tendency for stock returns to continue drifting in the direction of an earnings surprise after the public earnings announcement.

The literature support for the phenomenon is strong, but implementation risk is unusually high because valid measurement requires accurate point-in-time earnings events, surprise definitions, announcement timestamps and tradability timing.

## Established Literature Foundation

Ball and Brown (1968) established the foundational earnings-return association result and documented that abnormal returns continued to move after earnings news. Foster, Olsen and Shevlin (1984) further documented earnings-release anomalies and systematic post-announcement return behavior. Bernard and Thomas (1989, 1990) became the canonical PEAD references by framing the evidence as delayed price response versus risk premium and by linking the drift to investors' underreaction to earnings implications.

## Canonical Construct Description

The most common PEAD structure has three components:

1. An earnings announcement event.
2. An earnings surprise measure.
3. A post-announcement return drift window.

The usual empirical design ranks firms by earnings surprise, then compares subsequent abnormal returns between positive-surprise and negative-surprise firms.

## Measurement Families

Common earnings surprise definitions include:

- Standardized Unexpected Earnings (SUE) from time-series earnings models.
- Analyst forecast surprise using consensus expectations and actual reported EPS.
- Combined earnings surprise and revenue surprise measures.
- Announcement-window price reaction as a market-based proxy for surprise.

The literature does not treat these definitions as interchangeable. Livnat and Mendenhall (2006) report materially different drift magnitudes depending on whether surprise is measured using analyst forecasts or time-series earnings models.

## Theoretical Explanations

Behavioural explanations:

- Investor underreaction to earnings news.
- Slow diffusion of information.
- Anchoring on prior expectations.
- Limited attention.

Risk-based explanations:

- Drift may compensate for unidentified risk exposures.
- Risk-adjustment model misspecification can affect measured abnormal returns.

Limits-to-arbitrage explanations:

- Transaction costs, liquidity, short-sale constraints and implementation frictions may prevent full arbitrage.
- Chordia et al. emphasize liquidity and trading-cost considerations as important for understanding PEAD persistence.

## Empirical Evidence Summary

Strong evidence:

- PEAD has been repeatedly documented in US equity literature over multiple decades.
- Drift direction is generally linked to the sign and magnitude of earnings surprise.
- The anomaly has a clear event anchor and mechanism interpretation.

Moderate evidence:

- PEAD persists across some alternative definitions and samples.
- Analyst-based surprise measures can produce stronger drift than time-series surprise definitions.

Conflicting or limited evidence:

- Drift magnitudes vary by sample period, data source, liquidity, transaction costs and surprise definition.
- Some disaggregated or modern studies question whether portfolio-level drift reflects broad firm-level persistence.
- Publication and crowding effects may reduce realized predictability.

## Implementation Risk

PEAD has one of the highest data-integrity burdens among candidate edge constructs.

Unsafe implementation choices can create look-ahead bias through:

- Using revised analyst estimates.
- Using earnings dates without announcement times.
- Treating after-close earnings as tradable on the same close.
- Using fiscal period end date instead of actual announcement date.
- Using restated Compustat values without point-in-time controls.
- Ignoring delisted firms and survivorship bias.

## LR-001 Conclusion

PEAD is scientifically mature and worthy of construct definition.

However, CD-001 must prioritize data integrity over convenience. If reliable point-in-time earnings announcement and surprise data cannot be specified, the construct should either be narrowly defined around safe observable proxies or paused.

## Next Stage

Proceed to:

**PEAD-001 / CD-001 Construct Definition**
