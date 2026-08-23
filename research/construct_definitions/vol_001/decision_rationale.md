# Decision Rationale

## Final Decision

Select and freeze:

```text
US Equity Market Daily Yang-Zhang Volatility State
```

## Why This Definition Was Selected

The selected construct balances five priorities:

1. **Literature support**

Yang-Zhang belongs to the established range-based realized-volatility estimator family documented in LR-001.

2. **Theoretical clarity**

It measures realized market variation using overnight and intraday OHLC components.

3. **Operational reproducibility**

It can be computed deterministically from daily SPY OHLC data.

4. **Current-state fit**

A 20-day trailing estimate provides a current market volatility-state measure without requiring model fitting.

5. **Implementation simplicity**

It avoids option data, intraday sampling decisions and parametric optimization.

## Why 20 Days

The 20-day window approximates one trading month.

This is an operational convention, not an optimized parameter.

## Why 252 Days

The 252-day normalization window approximates one trading year.

This is an operational convention, not an optimized parameter.

## Why SPY

SPY is selected as a liquid, accessible and reproducible broad US equity market proxy.

This does not imply SPY is the only possible market proxy.

## Decision Boundary

This decision does not claim:

- predictive validity
- economic utility
- alpha
- production suitability
- superiority over all volatility estimators

It only freezes one scientifically defensible construct for the next lifecycle stages.

