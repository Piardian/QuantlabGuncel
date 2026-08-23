# OPT-001 / LR-001

# Methodology Comparison

## Purpose

Compare common methodologies used to extract information from option prices.

No implementation is selected in LR-001.

## VIX-Style Model-Free Implied Volatility

Description:

Aggregates option prices across strikes to infer expected variance over a fixed horizon.

Strengths:

- official methodology,
- public index availability,
- high practitioner recognition,
- index-level simplicity.

Weaknesses:

- index-level only unless extended,
- risk-neutral not physical expectation,
- can include risk premium and hedging demand.

## At-The-Money Implied Volatility

Description:

Uses implied volatility from options near the current underlying price.

Strengths:

- simple,
- widely available,
- intuitive.

Weaknesses:

- model-dependent,
- ignores skew and tails,
- sensitive to maturity and quote selection.

## Variance Risk Premium

Description:

Compares implied variance with realized or expected physical variance.

Strengths:

- strong academic literature,
- separates implied volatility from realized volatility context,
- economically interpretable as risk compensation.

Weaknesses:

- requires physical variance estimate,
- measurement choices are controversial,
- not purely option-implied if realized variance is included.

## Risk-Neutral Moment Estimation

Description:

Uses option prices across strikes to estimate risk-neutral variance, skewness, and kurtosis.

Strengths:

- theoretically rich,
- captures tail and asymmetry.

Weaknesses:

- data-intensive,
- sensitive to strike coverage,
- interpolation and extrapolation choices matter.

## Volatility Smirk Slope

Description:

Measures the relative expensiveness of downside puts versus ATM or upside options.

Strengths:

- captures downside protection demand,
- empirically studied in cross-section.

Weaknesses:

- requires security-level options data,
- sensitive to liquidity and moneyness rules.

## Put-Call Parity Deviations

Description:

Compares call and put implied volatilities or prices after parity adjustments.

Strengths:

- connected to informed trading and constraints literature.

Weaknesses:

- highly microstructure-sensitive,
- requires careful dividend, borrow, and exercise assumptions.

## Implied Correlation

Description:

Compares index implied volatility with component implied volatilities.

Strengths:

- distinct from realized correlation,
- relevant for systemic risk and dispersion.

Weaknesses:

- requires component option data or official index series,
- methodology-specific.

## Methodological Conclusion

For a first OPT-001 construct, the most reproducible paths are:

- public index-level implied volatility,
- public index-level term structure,
- or variance risk premium using clearly defined realized variance.

More complex cross-sectional option constructs may require separate later programs.

