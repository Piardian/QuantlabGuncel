# OPT-001 / CD-001

# Decision Rationale

## Decision

Select:

```text
US Equity Index Option-Implied Volatility State
```

using:

```text
VIXCLS
```

## Why This Definition Best Fits OPT-001

LR-001 found that options-implied information is scientifically mature but too broad.

The VIXCLS definition is selected because it:

- directly reflects option-implied volatility,
- has official methodology support,
- is public and reproducible,
- avoids full option-surface implementation complexity,
- is daily and market-level,
- is clearly distinct from realized volatility even if empirically related.

## Why Not A More Complex Construct First

Risk-neutral skewness, variance risk premium, smirk slope, implied correlation, and put-call parity deviations are scientifically important, but they introduce substantially more data and implementation assumptions.

CD-001 prioritizes measurement reliability and reproducibility for the first options-implied construct.

## Relationship To VOL-001

VOL-001 measures realized volatility from SPY OHLC data.

OPT-001 measures options-implied volatility from SPX option prices via VIX.

The two may be empirically related, but they represent different information sets.

## Scientific Boundary

This decision is not a claim that VIX is predictive, profitable, economically useful, or superior to alternative options-implied constructs.

It is only a construct-definition decision.

