# OPT-001 / LR-001

# Empirical Findings

## Scope

This document summarizes findings reported in the literature. It does not perform independent predictive validation.

## Implied Volatility And Realized Volatility

The literature generally finds that implied volatility contains information about future realized volatility, but survey evidence reports no universal consensus that implied volatility always dominates historical time-series methods.

Evidence classification: Moderate to strong, with conflicting findings.

## Variance Risk Premium

Variance risk premium has substantial academic support as a priced risk construct. Studies report relationships with expected returns and risk compensation, but measurement is sensitive to how implied and physical variance are estimated.

Evidence classification: Strong, with measurement caveats.

## Risk-Neutral Skewness And Moments

Risk-neutral moments derived from option prices have strong theoretical support. Empirical work connects risk-neutral skewness and higher moments to equity risk characteristics.

Evidence classification: Strong theoretical support; empirical implementation is data-sensitive.

## Volatility Smirk

Research reports that the shape of individual option volatility smirks can contain information about future equity outcomes, especially negative information or downside risk.

Evidence classification: Moderate to strong.

## Put-Call Parity Deviations

Studies report that deviations from put-call parity can contain information about future stock returns. However, implementation requires careful treatment of frictions, dividends, and quote quality.

Evidence classification: Moderate to strong but implementation-sensitive.

## Implied Correlation

Cboe implied correlation methodology interprets index and component option pricing differences as market-implied co-movement. Practitioner use is strongest in dispersion and risk contexts.

Evidence classification: Moderate.

## Practitioner Evidence

Practitioner literature widely uses VIX, VIX term structure, put-call ratios, skew indexes, and volatility products for monitoring market risk and hedging demand.

Evidence classification: Moderate, but should be separated from peer-reviewed evidence.

## Empirical Conclusion

The options-implied domain contains multiple promising constructs. The strongest CD-001 candidates are those with:

- strong theoretical foundation,
- public reproducible data,
- clear interpretation,
- limited microstructure complexity.

