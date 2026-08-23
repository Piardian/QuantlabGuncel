# OPT-001 / LR-001

# Theoretical Foundations

## Core Concept

Options are contingent claims. Their prices encode market compensation for future uncertainty, downside protection, volatility exposure, and state-contingent payoffs.

This makes option prices fundamentally different from historical realized returns.

## Risk-Neutral Pricing

Option prices imply a risk-neutral distribution, not a direct physical probability distribution.

This distinction is central:

```text
option-implied information = priced risk-neutral information
```

not necessarily:

```text
true forecast of real-world outcomes
```

## Volatility Expectation Channel

Implied volatility reflects the level of volatility priced by options. VIX-style measures aggregate option prices into an index-level expectation of near-term volatility.

Evidence status: Strong.

## Volatility Risk Premium Channel

The difference between implied and realized variance can represent compensation for bearing volatility risk or crash risk.

Evidence status: Strong.

## Tail-Risk And Skewness Channel

OTM put prices and the shape of the volatility smirk may reflect demand for downside protection and pricing of crash risk.

Evidence status: Strong theoretical support, moderate to strong empirical support.

## Information Asymmetry Channel

Options can be attractive to informed traders because they provide leverage, limited downside, and directional or volatility-specific exposure.

This supports studies of smirk, put-call parity deviations, and option volume.

Evidence status: Moderate.

## Hedging Demand Channel

Institutional hedging demand can affect index option prices, skew, and implied volatility levels.

Evidence status: Moderate to strong.

## Correlation Pricing Channel

Index option prices reflect both component volatility and expected co-movement. Implied correlation constructs attempt to isolate priced diversification/correlation expectations.

Evidence status: Moderate.

## Theoretical Implication For CD-001

CD-001 must choose which theoretical channel OPT-001 is meant to represent.

It cannot simultaneously represent volatility expectation, variance risk premium, skew, tail risk, correlation, and option flow unless explicitly defined as a composite construct.

