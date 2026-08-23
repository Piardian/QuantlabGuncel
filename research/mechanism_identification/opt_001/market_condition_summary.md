# OPT-001 / MI-001

# Market Condition Summary

## Descriptive State Conditions

| state_bucket | observations | opt001_vix_close_mean | opt001_vix_close_median | spy_abs_return_1d_mean | spy_realized_vol_20d_ann_mean | spy_range_pct_mean | spy_drawdown_252d_mean | spy_volume_ratio_20d_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_OPT_IMPLIED_VOL | 848 | 29.050436 | 25.705000 | 0.015724 | 0.279734 | 0.023776 | -0.111156 | 1.165705 |
| LOW_OPT_IMPLIED_VOL | 1325 | 15.248091 | 14.330000 | 0.004700 | 0.111159 | 0.007768 | -0.021883 | 0.920930 |
| MID_OPT_IMPLIED_VOL | 2356 | 19.295335 | 17.520000 | 0.007169 | 0.152934 | 0.011567 | -0.060159 | 0.997815 |

## State Transition Profile

| prev_state_bucket | opt001_state_bucket | count | from_total | pct_from_state |
| --- | --- | --- | --- | --- |
| HIGH_OPT_IMPLIED_VOL | HIGH_OPT_IMPLIED_VOL | 722 | 848 | 0.851415 |
| HIGH_OPT_IMPLIED_VOL | MID_OPT_IMPLIED_VOL | 126 | 848 | 0.148585 |
| LOW_OPT_IMPLIED_VOL | HIGH_OPT_IMPLIED_VOL | 2 | 1324 | 0.001511 |
| LOW_OPT_IMPLIED_VOL | LOW_OPT_IMPLIED_VOL | 1136 | 1324 | 0.858006 |
| LOW_OPT_IMPLIED_VOL | MID_OPT_IMPLIED_VOL | 186 | 1324 | 0.140483 |
| MID_OPT_IMPLIED_VOL | HIGH_OPT_IMPLIED_VOL | 123 | 2356 | 0.052207 |
| MID_OPT_IMPLIED_VOL | LOW_OPT_IMPLIED_VOL | 189 | 2356 | 0.080221 |
| MID_OPT_IMPLIED_VOL | MID_OPT_IMPLIED_VOL | 2044 | 2356 | 0.867572 |

## Interpretation

The state profile is coherent with an options-implied volatility mechanism. Higher OPT-001 states correspond to stressed or turbulent contemporaneous market environments, while lower OPT-001 states correspond to calmer contemporaneous market environments.

The transition profile is descriptive only and does not imply predictive behavior.
