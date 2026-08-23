# OPT-001 / LR-001

# Options-Implied Market Information Literature Review

## Study Scope

This literature review evaluates Options-Implied Market Information as a financial construct family.

This stage is descriptive only. It does not define the final construct, select variables for implementation, test predictive validity, or assess economic value.

## Executive Finding

Options-implied market information is strongly supported by academic and practitioner literature as a distinct family of market constructs.

The literature supports option prices as a source of risk-neutral, forward-looking information about:

- expected volatility,
- variance compensation,
- risk-neutral skewness,
- tail risk,
- implied correlation,
- hedging demand,
- information asymmetry,
- market stress expectations.

However, the literature does not support treating all option-implied measures as a single construct. OPT-001 must be narrowed in CD-001.

## Evidence Classification

### Strongly Supported By Literature

- Option prices contain forward-looking risk-neutral information.
- Implied volatility is a central market expectation measure, especially through VIX-style methodology.
- Variance risk premium is a major research construct.
- Risk-neutral moments can be inferred from option prices under established frameworks.
- Option-implied skew/smirk contains information beyond historical return measures.

### Moderately Supported

- Option-implied measures can improve risk forecasting in some settings.
- Implied correlation represents market expectations about index-component co-movement.
- Put-call parity deviations can reflect option-market information or demand imbalance.

### Conflicting Or Limited Evidence

- Implied volatility does not universally dominate historical volatility for realized volatility forecasting.
- Cross-sectional option-surface constructs require high-quality options data and careful microstructure controls.
- Option-implied measures are risk-neutral, not direct physical probability forecasts.
- Practitioner measures such as put-call ratios are widely used but less theoretically precise.

## Main Literature Streams

## 1. Implied Volatility Level

VIX-style constructs use option prices to represent expected near-term volatility. Official methodology documents describe VIX as an options-based volatility index rather than a stock-price index.

## 2. Volatility Risk Premium

Variance risk premium literature studies the difference between option-implied variation and realized or expected physical variation.

## 3. Risk-Neutral Moments

Bakshi, Kapadia, and Madan provide foundational tools for estimating risk-neutral skewness and higher moments from option prices.

## 4. Volatility Smirk And Skew

Research on individual option smirks reports that downside option pricing contains information about future equity risk and negative information flow.

## 5. Put-Call Parity Deviations

The literature reports that deviations between call and put implied volatilities can contain information, but interpretation is sensitive to frictions and implementation details.

## 6. Implied Correlation

Cboe implied correlation methodology interprets relative pricing between index options and component options as market-implied correlation.

## LR-001 Decision

OPT-001 should proceed to CD-001.

However, CD-001 must select one narrow options-implied construct rather than freezing the entire options-implied information family.

## Boundary

This review does not claim predictive validity, trading edge, alpha, economic value, or production suitability.

