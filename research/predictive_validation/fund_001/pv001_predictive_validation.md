# FUND-001 / PV-001: Predictive Validation

## Scope

This study evaluates predictive validity only. It does not evaluate alpha, trading returns, strategy profitability, portfolio performance, or economic value.

## Predictor

```text
fund001_zscore_252d at date t
```

## Future Targets

- Future SPY realized volatility over 5, 20, and 60 trading days.
- Future SPY drawdown risk over 5, 20, and 60 trading days.
- Future LIQ-001 liquidity stress over 5, 20, and 60 trading days.
- Future CRD-001 credit stress over 5, 20, and 60 trading days.

## Overall Result

```text
Partially supported
```

## Hypothesis-Level Summary

| hypothesis | target_family | evaluated_horizons | supported_horizons | partially_supported_horizons | classification |
| --- | --- | --- | --- | --- | --- |
| H1 | future_realized_vol | 5,20,60 | 3 | 0 | Supported by evidence |
| H2 | future_drawdown_risk | 5,20,60 | 3 | 0 | Supported by evidence |
| H3 | future_liq_stress | 5,20,60 | 3 | 0 | Supported by evidence |
| H4 | future_credit_stress | 5,20 | 2 | 0 | Partially supported |

## Metric Summary

| hypothesis | target | horizon_days | observations | spearman_ic | ci_95_low | ci_95_high | auc_for_top_20pct_future_risk | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | future_realized_vol | 5 | 3433 | 0.194617 | 0.162377 | 0.226293 | 0.623019 | Supported by evidence |
| H2 | future_drawdown_risk | 5 | 3433 | 0.114101 | 0.081679 | 0.149563 | 0.597063 | Supported by evidence |
| H3 | future_liq_stress | 5 | 3166 | 0.318333 | 0.281862 | 0.351628 | 0.741893 | Supported by evidence |
| H4 | future_credit_stress | 5 | 260 | -0.200690 | -0.307232 | -0.077943 | 0.473095 | Partially supported |
| H1 | future_realized_vol | 20 | 3423 | 0.211086 | 0.175380 | 0.242869 | 0.640527 | Supported by evidence |
| H2 | future_drawdown_risk | 20 | 3423 | 0.156485 | 0.124260 | 0.188543 | 0.576272 | Supported by evidence |
| H3 | future_liq_stress | 20 | 3156 | 0.353979 | 0.321083 | 0.385791 | 0.717558 | Supported by evidence |
| H4 | future_credit_stress | 20 | 252 | -0.211126 | -0.325852 | -0.096744 | 0.466731 | Partially supported |
| H1 | future_realized_vol | 60 | 3404 | 0.174422 | 0.140999 | 0.204968 | 0.622956 | Supported by evidence |
| H2 | future_drawdown_risk | 60 | 3404 | 0.159267 | 0.127057 | 0.193915 | 0.585220 | Supported by evidence |
| H3 | future_liq_stress | 60 | 3137 | 0.310684 | 0.279770 | 0.345156 | 0.638136 | Supported by evidence |
| H4 | future_credit_stress | 60 | 231 | -0.068757 | -0.180486 | 0.055719 | 0.522199 | Partially supported |

## Interpretation

FUND-001 shows meaningful but target-dependent predictive information. Evidence is strongest for future realized volatility, future drawdown risk, and future liquidity stress.

Credit-stress evidence is only partially supported because overlap with CRD-001 is short and the observed association is directionally negative over the available sample.

## Boundary

No economic or trading conclusion is made.
