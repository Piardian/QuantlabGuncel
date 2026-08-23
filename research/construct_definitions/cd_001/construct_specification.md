# Construct Specification

## Construct Name

**US Equity Market Regime**

## Construct Type

Latent binary regime

## Market Proxy

SPY is the canonical market proxy for the construct definition.

## Inputs

1. Daily SPY close-to-close log return
2. 20-day realized volatility of SPY returns, annualized

## Model

The construct is implemented as a **two-state Gaussian Hidden Markov Model** with:

- first-order Markov dependence
- state-specific mean return
- state-specific return variance
- state-specific realized volatility behavior

## State Interpretation

- **State 1:** Expansion / Risk-On
- **State 2:** Stress / Risk-Off

The labels are assigned after estimation using the fitted state characteristics.

## Output

Each trading day receives:

- a regime label
- a posterior probability for each state

## Non-Goals

This construct does not attempt to:

- maximize predictability
- maximize trading returns
- optimize thresholds
- explain every macro regime shift
- produce a universal regime taxonomy

