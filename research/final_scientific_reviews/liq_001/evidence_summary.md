# LIQ-001 Evidence Summary

## Scope

This document synthesizes completed LIQ-001 evidence only. It does not introduce new empirical results.

## Stage Evidence

### RP-001

Classification: **GO**

Market Liquidity was judged sufficiently important, distinct, measurable and literature-supported to justify a standalone research program.

### LR-001

Classification: **Supported by literature**

The literature supports liquidity as a multidimensional construct involving tightness, depth, immediacy, breadth, resiliency and price impact. LIQ-001 later selected only the price-impact dimension.

### CD-001

Classification: **Construct frozen**

The selected construct was **US Equity Aggregate Daily Illiquidity**, using an Amihud-style proxy:

```text
illiquidity_i,t = abs(log_return_i,t) / dollar_volume_i,t
aggregate_illiquidity_t = median(illiquidity_i,t)
```

The construct includes 20-day smoothing, 252-day z-score normalization and coverage diagnostics.

### IM-001

Classification: **Successfully implemented**

The implementation created the required feature pipeline, aggregate model, inference helpers, configuration, validation script and tests. Deterministic execution was verified through identical output hashes across repeated runs.

### CV-001

Classification: **Partially supported**

LIQ-001 produced internally coherent output with the expected schema, minimum eligible security count of 50, mean coverage ratio of 0.9483 and plausible stress clustering around March 2020. The capped 59-symbol validation universe limited final strength.

### MI-001

Classification: **Partially supported**

The construct behaved like an aggregate price-impact liquidity stress measure. High LIQ-001 periods were associated with higher realized volatility, larger absolute market moves, deeper drawdown context and higher overlap with MR-001 STRESS states.

### HV-001

Classification: **Partially supported**

Four mechanism hypotheses were supported and one negative-control style hypothesis was partially supported. Evidence supported the liquidity-stress mechanism, while the coverage artifact test remained only partially resolved.

### PV-001

Classification: **Supported by evidence**

LIQ-001 showed predictive information for future realized volatility, future absolute market movement and future MR-001 STRESS occurrence. Future drawdown-risk evidence was positive but weaker and classified as partially supported.

### EV-001

Classification: **Partially supported**

Economic utility was strongest for regime-aware portfolio risk control. Risk budgeting, volatility targeting and hedge activation were partially supported due to tradeoffs across return, volatility, drawdown and downside-adjusted metrics.

### CC-001

Classification: **Medium-High scientific maturity**

LIQ-001 was classified as a **Liquidity Stress / Risk Control Construct**, not as alpha, direct return prediction or exact execution-cost modeling.

## Integrated Evidence

The completed evidence body supports LIQ-001 as a risk-state construct whose strongest validated role is liquidity-stress detection and risk-control support.

The evidence does not support treating LIQ-001 as a standalone trading signal, alpha factor, precise transaction-cost proxy or intraday liquidity model.
