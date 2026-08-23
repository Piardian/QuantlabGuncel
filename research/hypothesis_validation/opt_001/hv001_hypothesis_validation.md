# OPT-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the mechanism hypotheses generated in MI-001 are empirically supported.

This stage evaluates explanatory validity only. No predictive, alpha, profitability, trading-performance, or economic utility claim is made.

## Overall Classification

```text
Supported by evidence
```

## Results

| hypothesis | feature | group_a_count | group_b_count | difference | ci_low | ci_high | cohens_d | permutation_pvalue | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1A | spy_realized_vol_20d_ann | 831 | 1325 | 0.168576 | 0.155954 | 0.182028 | 1.359768 | 0.000250 | Supported by evidence |
| H1B | spy_abs_return_1d | 847 | 1325 | 0.011024 | 0.009940 | 0.012197 | 1.035289 | 0.000250 | Supported by evidence |
| H1C | spy_range_pct | 848 | 1325 | 0.016007 | 0.014864 | 0.017188 | 1.430132 | 0.000250 | Supported by evidence |
| H2 | spy_drawdown_252d | 832 | 1325 | -0.089273 | -0.096392 | -0.082395 | -1.260772 | 0.000250 | Supported by evidence |
| H3 | calm_composite | 1325 | 848 | -1.349797 | -1.445521 | -1.256793 | -1.482175 | 0.000250 | Supported by evidence |
| H4 | construct_scope_audit | 0 | 0 |  |  |  |  |  | Supported by evidence |

## Interpretation

The evidence supports the MI-001 mechanism that OPT-001 represents an index option-implied uncertainty / expected volatility state. High OPT-001 states are associated with materially higher realized market volatility, larger same-day market movement, wider market ranges, and deeper drawdown context. Low OPT-001 states are associated with calmer realized market conditions.

H4 is supported as a construct-boundary statement: VIXCLS alone cannot separate pure expected volatility from volatility risk premium, fear, risk aversion, hedging demand, or related option-market pricing components.

The evidence is not interpreted as prediction or economic utility.
