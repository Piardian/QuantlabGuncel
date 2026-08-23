# OPT-001 / PV-001: Predictive Validation

## Purpose

Evaluate whether OPT-001 contains predictive information about future market risk variables.

This is predictive validation only. No alpha, trading-performance, profitability, Sharpe, CAGR, portfolio, or economic utility claim is made.

## Overall Classification

```text
Mixed but meaningful
```

## Hypothesis Classifications

| hypothesis | supported_metrics | partial_metrics | not_supported_metrics | inconclusive_metrics | classification |
| --- | --- | --- | --- | --- | --- |
| H1 | 6 | 0 | 0 | 0 | Supported by evidence |
| H2 | 6 | 0 | 0 | 0 | Supported by evidence |
| H3 | 3 | 0 | 0 | 0 | Supported by evidence |
| H4 | 0 | 3 | 0 | 0 | Inconclusive |

## Predictive Metrics

| hypothesis | horizon | target_description | metric | estimate | ci_low | ci_high | baseline | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 5 | future realized market volatility | spearman_ic | 0.507362 | 0.483976 | 0.531330 | 0.000000 | Supported by evidence |
| H2 | 5 | future drawdown risk | spearman_ic | 0.156438 | 0.128355 | 0.185487 | 0.000000 | Supported by evidence |
| H3 | 5 | future absolute market movement | spearman_ic | 0.358040 | 0.332444 | 0.385392 | 0.000000 | Supported by evidence |
| H4 | 5 | future directional market return | spearman_ic | 0.064775 | 0.033305 | 0.095096 | 0.000000 | Partially supported |
| H1 | 5 | top-quintile future realized volatility | auc_top_quintile | 0.806794 | 0.790667 | 0.822862 | 0.500000 | Supported by evidence |
| H2 | 5 | top-quintile future drawdown depth | auc_top_quintile | 0.671944 | 0.652267 | 0.690962 | 0.500000 | Supported by evidence |
| H1 | 20 | future realized market volatility | spearman_ic | 0.466887 | 0.441722 | 0.490967 | 0.000000 | Supported by evidence |
| H2 | 20 | future drawdown risk | spearman_ic | 0.173499 | 0.144532 | 0.201753 | 0.000000 | Supported by evidence |
| H3 | 20 | future absolute market movement | spearman_ic | 0.257695 | 0.230304 | 0.284936 | 0.000000 | Supported by evidence |
| H4 | 20 | future directional market return | spearman_ic | 0.072263 | 0.040839 | 0.099383 | 0.000000 | Partially supported |
| H1 | 20 | top-quintile future realized volatility | auc_top_quintile | 0.808725 | 0.794058 | 0.824207 | 0.500000 | Supported by evidence |
| H2 | 20 | top-quintile future drawdown depth | auc_top_quintile | 0.654583 | 0.633978 | 0.673457 | 0.500000 | Supported by evidence |
| H1 | 60 | future realized market volatility | spearman_ic | 0.378347 | 0.351881 | 0.404693 | 0.000000 | Supported by evidence |
| H2 | 60 | future drawdown risk | spearman_ic | 0.139122 | 0.110647 | 0.168368 | 0.000000 | Supported by evidence |
| H3 | 60 | future absolute market movement | spearman_ic | 0.191456 | 0.161291 | 0.218870 | 0.000000 | Supported by evidence |
| H4 | 60 | future directional market return | spearman_ic | 0.068166 | 0.038170 | 0.095361 | 0.000000 | Partially supported |
| H1 | 60 | top-quintile future realized volatility | auc_top_quintile | 0.750977 | 0.732067 | 0.769378 | 0.500000 | Supported by evidence |
| H2 | 60 | top-quintile future drawdown depth | auc_top_quintile | 0.653146 | 0.632985 | 0.672759 | 0.500000 | Supported by evidence |

## Interpretation

OPT-001 shows predictive information for future realized volatility, future absolute market movement, and future drawdown risk. Evidence for future directional market returns is weak and classified as inconclusive because the observed associations are small and this study does not evaluate directional trading value.

The evidence should be interpreted as risk-state predictive information, not as a trading signal or alpha source.
