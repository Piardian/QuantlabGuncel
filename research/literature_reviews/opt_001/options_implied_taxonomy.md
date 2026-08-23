# OPT-001 / LR-001

# Options-Implied Taxonomy

## Purpose

This document maps options-implied construct families found in the literature.

No official OPT-001 construct is selected in LR-001.

## Family 1: Implied Volatility Level

Measures the level of volatility priced by options.

Examples:

- VIX,
- VIX9D,
- VIX3M,
- ATM implied volatility,
- model-free implied variance.

Primary construct meaning:

```text
market-priced expected volatility
```

Evidence strength: Strong.

## Family 2: Implied Volatility Term Structure

Measures how option-implied volatility differs across maturities.

Examples:

- short-term vs medium-term implied volatility,
- VIX futures term structure,
- contango/backwardation.

Primary construct meaning:

```text
time profile of priced uncertainty
```

Evidence strength: Moderate to strong.

## Family 3: Volatility / Variance Risk Premium

Measures compensation for bearing volatility or variance risk.

Examples:

- implied variance minus realized variance,
- variance swap premium,
- VIX squared minus realized variance.

Primary construct meaning:

```text
priced compensation for volatility risk
```

Evidence strength: Strong, but measurement choices are important.

## Family 4: Risk-Neutral Skewness And Higher Moments

Measures asymmetry and tail shape embedded in option prices.

Examples:

- Bakshi-Kapadia-Madan skewness,
- risk-neutral kurtosis,
- option-implied tail loss.

Primary construct meaning:

```text
priced asymmetry and tail risk
```

Evidence strength: Strong theoretical support; data-intensive.

## Family 5: Volatility Smirk / Smile Shape

Measures the slope or curvature of implied volatility across strikes.

Examples:

- put-wing steepness,
- OTM put IV minus ATM IV,
- smirk slope.

Primary construct meaning:

```text
downside protection demand and negative information pricing
```

Evidence strength: Moderate to strong.

## Family 6: Implied Correlation

Measures expected co-movement implied by index options and component options.

Examples:

- Cboe Implied Correlation Index,
- dispersion-implied correlation.

Primary construct meaning:

```text
market-priced systemic co-movement
```

Evidence strength: Moderate.

## Family 7: Put-Call Parity Deviations

Measures deviations in relative call and put pricing.

Examples:

- call-put implied volatility spread,
- put-call parity deviations after frictions.

Primary construct meaning:

```text
option-market demand imbalance, constraints, or informed trading
```

Evidence strength: Moderate to strong but implementation-sensitive.

## Family 8: Option Flow And Positioning

Measures trading behavior rather than option-implied risk-neutral prices directly.

Examples:

- put-call volume ratio,
- open interest,
- dealer gamma estimates,
- option volume imbalance.

Primary construct meaning:

```text
derivatives-market positioning pressure
```

Evidence strength: Mixed and practitioner-heavy.

## Taxonomy Conclusion

The best-supported academic subfamilies are:

- implied volatility level,
- variance risk premium,
- risk-neutral moments/skew,
- volatility smirk,
- put-call parity deviations.

The most operationally simple public-data path is likely an index-level implied volatility or variance-premium construct.

