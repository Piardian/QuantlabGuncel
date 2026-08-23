# OPT-001 / HV-001

# Robustness Analysis

## Top 1 Percent VIX Removal

| test | feature | high_count | low_count | high_mean | low_mean | difference |
| --- | --- | --- | --- | --- | --- | --- |
| remove_top_1pct_vix | spy_realized_vol_20d_ann | 785 | 1325 | 0.249894 | 0.111159 | 0.138735 |
| remove_top_1pct_vix | spy_abs_return_1d | 801 | 1325 | 0.014055 | 0.004700 | 0.009355 |
| remove_top_1pct_vix | spy_range_pct | 802 | 1325 | 0.021324 | 0.007768 | 0.013556 |
| remove_top_1pct_vix | spy_drawdown_252d | 786 | 1325 | -0.096660 | -0.021883 | -0.074776 |

## Interpretation

After removing the top 1 percent of raw VIX observations, high OPT states remain associated with higher realized volatility, larger absolute movement, wider range, and deeper drawdown context than low OPT states.

This suggests the explanatory mechanism is not driven solely by the most extreme VIX observations.
