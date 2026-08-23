# Volatility Taxonomy

## Purpose

Classify the major volatility constructs found in the literature.

## Family A: Historical Realized Volatility

Definition:

Volatility measured from historical realized returns.

Common forms:

- rolling close-to-close standard deviation
- rolling variance of log returns
- realized volatility from intraday returns

Evidence category:

**Strongly supported by literature**

Strength:

Simple, reproducible and directly tied to observed price variation.

Limitation:

Daily close-to-close versions ignore intraday variation and overnight decomposition.

## Family B: Range-Based Volatility

Definition:

Volatility estimated from high-low or OHLC prices.

Common forms:

- Parkinson
- Garman-Klass
- Rogers-Satchell
- Yang-Zhang

Evidence category:

**Strongly supported by literature**

Strength:

Uses more daily price-path information than close-to-close returns.

Limitation:

Estimators differ in assumptions about drift, jumps, opening gaps and continuous trading.

## Family C: Conditional Volatility

Definition:

Latent or model-implied current variance conditional on past information.

Common forms:

- ARCH
- GARCH
- asymmetric GARCH variants
- stochastic volatility models

Evidence category:

**Strongly supported by literature**

Strength:

Directly models volatility persistence and clustering.

Limitation:

Requires model fitting and parameter assumptions.

## Family D: Implied Volatility

Definition:

Expected future volatility inferred from option prices.

Common forms:

- VIX
- VIX-style volatility indices
- option-implied volatility surfaces

Evidence category:

**Strongly supported by literature and practitioner methodology**

Strength:

Forward-looking and market-priced.

Limitation:

Includes volatility risk premia and depends on liquid option markets.

## Family E: ATR-Derived Volatility

Definition:

Range and gap magnitude based on True Range.

Common forms:

- ATR
- ATR percent
- normalized true range

Evidence category:

**Moderately supported**

Strength:

Operationally simple and common in practitioner risk systems.

Limitation:

ATR is not a formal variance estimator.

## Family F: Cross-Sectional Volatility / Dispersion

Definition:

Volatility measured across securities at a point in time.

Common forms:

- dispersion of stock returns
- cross-sectional standard deviation
- sector or constituent dispersion

Evidence category:

**Moderately supported**

Strength:

Captures breadth of market disagreement and heterogeneity.

Limitation:

Measures cross-sectional dispersion, not time-series market volatility.

## Taxonomy Conclusion

The literature does not define volatility as one universal scalar. It supports multiple constructs sharing a common theme of return variation.

CD-001 must select one narrow family and explicitly reject the others for the current VOL-001 lifecycle.

