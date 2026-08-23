# Construct Assumptions

## 1. SPY Represents Broad US Equity Market Volatility

VOL-001 assumes SPY daily OHLC data is an acceptable broad US equity market proxy.

Classification:

**Supported by evidence for operational proxy use; still an assumption.**

## 2. Daily OHLC Data Is Sufficient for This Construct

VOL-001 intentionally uses daily OHLC data rather than intraday or options data.

This assumes a daily volatility-state sensor is scientifically useful even though it does not measure high-frequency realized variance or option-implied expectations.

Classification:

**Partially supported.**

## 3. Yang-Zhang Is Appropriate for Daily Realized Volatility State

The selected estimator assumes the Yang-Zhang framework is appropriate for combining overnight gap variation and intraday OHLC range variation.

Classification:

**Supported by literature.**

## 4. 20 Trading Days Represents Current State

The 20-day window is used as an approximate one-month current volatility state.

Classification:

**Operational convention; not an optimized parameter.**

## 5. 252 Trading Days Represents Local Historical Context

The 252-day normalization window is used as an approximate one-year context for z-score and percentile state.

Classification:

**Operational convention; not an optimized parameter.**

## 6. Adjusted OHLC Consistency Is Required

VOL-001 assumes open, high, low and close are adjusted or normalized consistently.

If only adjusted close is available but raw open/high/low are not adjusted consistently, the implementation must explicitly normalize OHLC before computing returns.

Classification:

**Implementation-critical assumption.**

