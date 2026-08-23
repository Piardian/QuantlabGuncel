# PROF-001 / LR-001 Literature Review

## Purpose

Synthesize the scientific literature on Profitability / Quality as an expected-return construct family.

This review does not define the frozen PROF-001 construct, select accounting variables, implement code, run tests, backtest, optimize, or claim alpha.

## Primary Research Question

What does the current scientific literature collectively conclude about Profitability / Quality as an independent expected-return mechanism?

## High-Level Finding

Profitability / Quality is a mature and well-supported firm-characteristic family in empirical asset pricing. The strongest literature streams are:

- Gross profitability, especially Novy-Marx's gross profits-to-assets formulation.
- Operating profitability, incorporated into the Fama-French five-factor model.
- Profitability and investment in q-factor / investment CAPM frameworks.
- Broader Quality Minus Junk definitions combining profitability, growth, safety and payout.

The family is scientifically important but not monolithic. Gross profitability, operating profitability and quality composites are related but distinct constructs.

## Canonical Measurement Families

### Gross Profitability

Gross profitability generally measures gross profits scaled by total assets. The key intuition is that firms with high gross profits relative to assets are economically productive.

### Operating Profitability

Operating profitability is used in the Fama-French five-factor framework and usually reflects operating income relative to book equity or related book measures.

### q-Factor Profitability

The q-factor literature links expected returns to investment and profitability through investment-based asset-pricing theory.

### Quality Composite

Quality Minus Junk defines quality more broadly, combining profitability, growth, safety and payout characteristics.

## Theoretical Foundations

The literature offers several mechanisms:

- Productive firms may generate persistent cash flows.
- Investors may underprice quality when high-quality firms do not appear conventionally cheap.
- Investment theory links expected profitability and investment to expected returns.
- Quality may proxy for safer, more durable firm economics.
- Behavioural explanations emphasize mispricing of boring or expensive-looking high-quality firms.

## Empirical Evidence Summary

Strong evidence:

- Profitability is recognized as an important cross-sectional characteristic.
- Fama-French incorporate profitability into a major asset-pricing model.
- Novy-Marx documents gross profitability as an economically important return predictor.
- Quality Minus Junk documents a broader quality factor across the US and international markets.

Moderate evidence:

- Profitability definitions can be reproduced across several datasets and factor libraries.
- Open-source asset pricing projects include many profitability and quality-related signals.

Conflicting or limited evidence:

- Evidence strength depends on definition, universe, weighting, sector treatment and accounting-data handling.
- Quality composites can be harder to interpret because they combine multiple dimensions.
- Publication decay and multiple-testing concerns apply to the broader anomaly literature.

## Data Integrity Requirements

PROF-001 requires careful accounting-data governance.

Critical requirements:

- Point-in-time financial statement availability or conservative publication lag.
- Avoiding restated accounting values when they were not available historically.
- Correct fiscal period alignment.
- Security identifier mapping across accounting and price data.
- Handling missing or negative denominators.
- Sector-specific treatment, especially financial firms.
- Clear exclusion rules.

## LR-001 Conclusion

Profitability / Quality is scientifically mature and worthy of construct definition.

CD-001 should not freeze a broad "quality" composite by default. It should select one narrow, interpretable, reproducible construct unless the literature and data requirements justify a composite.

## Next Stage

Proceed to:

**PROF-001 / CD-001 Construct Definition**
