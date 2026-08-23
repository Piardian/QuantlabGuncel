# Alternative Definitions Review

## Purpose

Document which volatility definitions were considered and why they were not selected for this VOL-001 lifecycle.

## Selected

### Yang-Zhang Daily OHLC Realized Volatility

Decision:

**Selected**

Rationale:

- Strong literature support.
- Uses open, high, low and close.
- Incorporates overnight gap and intraday range components.
- Deterministic from daily data.
- Fits the question: "What is the current volatility state of the market?"

## Not Selected

### Close-to-Close Realized Volatility

Decision:

**Rejected for VOL-001**

Reason:

It is simple and strongly supported but ignores intraday range and overnight/intraday decomposition. It remains a valid alternative construct.

### High-Frequency Realized Volatility

Decision:

**Rejected for VOL-001**

Reason:

It is strongly supported but requires intraday data and introduces sampling-frequency and microstructure-noise decisions.

### Parkinson Estimator

Decision:

**Rejected for VOL-001**

Reason:

It uses high-low range but ignores open and close information and is less complete for gap-aware daily market state than Yang-Zhang.

### Garman-Klass Estimator

Decision:

**Rejected for VOL-001**

Reason:

It uses OHLC data but is less directly designed for opening jumps than Yang-Zhang.

### Rogers-Satchell Estimator

Decision:

**Rejected as standalone for VOL-001**

Reason:

It is valuable and is included inside Yang-Zhang, but the standalone construct would omit the full overnight/open-to-close decomposition.

### ATR-Derived Volatility

Decision:

**Rejected for VOL-001**

Reason:

ATR is practical and interpretable but is not a formal variance estimator.

### ARCH/GARCH Conditional Volatility

Decision:

**Rejected for VOL-001**

Reason:

Strong literature support, but requires parametric model fitting and estimation choices. This is less suitable for the first deterministic daily volatility-state sensor.

### VIX / Implied Volatility

Decision:

**Rejected for VOL-001**

Reason:

VIX is strongly supported as forward-looking implied volatility, but it measures option-market expectations and volatility risk premia rather than realized current volatility state.

### Cross-Sectional Volatility

Decision:

**Rejected for VOL-001**

Reason:

It measures dispersion across securities, not time-series volatility of the market proxy.

## Conclusion

The selected definition is not claimed to be universally superior.

It is selected because it is narrow, literature-supported, deterministic from daily OHLC data and aligned with the intended VOL-001 question.

