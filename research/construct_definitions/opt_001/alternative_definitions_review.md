# OPT-001 / CD-001

# Alternative Definitions Review

## Accepted Definition

```text
US Equity Index Option-Implied Volatility State
```

using:

```text
VIXCLS
```

## Alternative 1: Implied Volatility Term Structure

Decision: Rejected for OPT-001 CD-001.

Rationale:

- scientifically important,
- but requires multiple tenor series or futures curve construction,
- introduces more design choices than a first OPT construct needs.

## Alternative 2: Variance Risk Premium

Decision: Rejected.

Rationale:

- strong academic support,
- but requires a physical variance estimate,
- would mix options-implied information with realized volatility modeling,
- more suitable for a later OPT variant.

## Alternative 3: Risk-Neutral Skewness

Decision: Rejected.

Rationale:

- strong theoretical support,
- but requires option surface data, strike integration, and interpolation/extrapolation choices.

## Alternative 4: Implied Tail Risk

Decision: Rejected.

Rationale:

- theoretically important,
- but requires detailed option surface methodology and tail extraction assumptions.

## Alternative 5: Volatility Smirk / Smile Slope

Decision: Rejected.

Rationale:

- strong cross-sectional literature,
- but requires security-level option data and strict microstructure controls.

## Alternative 6: Implied Correlation

Decision: Rejected.

Rationale:

- scientifically distinct,
- but requires index and component option information or official implied-correlation series,
- overlaps with COR-001 and should be its own construct if researched.

## Alternative 7: Put-Call Parity Deviations

Decision: Rejected.

Rationale:

- meaningful academic literature,
- but highly sensitive to dividends, borrow, early exercise, bid-ask spreads, and quote quality.

## Alternative 8: Option Flow / Positioning

Decision: Rejected.

Rationale:

- practitioner relevance,
- but less direct as an option-implied risk-neutral price construct,
- often requires proprietary or vendor data.

## Summary

VIXCLS is selected because it is the narrowest, most reproducible, public, index-level options-implied construct with strong methodology support.

