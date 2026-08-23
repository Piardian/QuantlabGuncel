# OPT-001 / PV-001

# Baseline Comparison

Baselines are zero Spearman information coefficient for continuous targets and 0.5 AUC for top-quintile classification tasks.

| hypothesis | horizon | target_description | metric | estimate | baseline | ci_low | ci_high | classification | beats_baseline_directionally |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 5 | future realized market volatility | spearman_ic | 0.507362 | 0.000000 | 0.483976 | 0.531330 | Supported by evidence | True |
| H2 | 5 | future drawdown risk | spearman_ic | 0.156438 | 0.000000 | 0.128355 | 0.185487 | Supported by evidence | True |
| H3 | 5 | future absolute market movement | spearman_ic | 0.358040 | 0.000000 | 0.332444 | 0.385392 | Supported by evidence | True |
| H4 | 5 | future directional market return | spearman_ic | 0.064775 | 0.000000 | 0.033305 | 0.095096 | Partially supported | True |
| H1 | 5 | top-quintile future realized volatility | auc_top_quintile | 0.806794 | 0.500000 | 0.790667 | 0.822862 | Supported by evidence | True |
| H2 | 5 | top-quintile future drawdown depth | auc_top_quintile | 0.671944 | 0.500000 | 0.652267 | 0.690962 | Supported by evidence | True |
| H1 | 20 | future realized market volatility | spearman_ic | 0.466887 | 0.000000 | 0.441722 | 0.490967 | Supported by evidence | True |
| H2 | 20 | future drawdown risk | spearman_ic | 0.173499 | 0.000000 | 0.144532 | 0.201753 | Supported by evidence | True |
| H3 | 20 | future absolute market movement | spearman_ic | 0.257695 | 0.000000 | 0.230304 | 0.284936 | Supported by evidence | True |
| H4 | 20 | future directional market return | spearman_ic | 0.072263 | 0.000000 | 0.040839 | 0.099383 | Partially supported | True |
| H1 | 20 | top-quintile future realized volatility | auc_top_quintile | 0.808725 | 0.500000 | 0.794058 | 0.824207 | Supported by evidence | True |
| H2 | 20 | top-quintile future drawdown depth | auc_top_quintile | 0.654583 | 0.500000 | 0.633978 | 0.673457 | Supported by evidence | True |
| H1 | 60 | future realized market volatility | spearman_ic | 0.378347 | 0.000000 | 0.351881 | 0.404693 | Supported by evidence | True |
| H2 | 60 | future drawdown risk | spearman_ic | 0.139122 | 0.000000 | 0.110647 | 0.168368 | Supported by evidence | True |
| H3 | 60 | future absolute market movement | spearman_ic | 0.191456 | 0.000000 | 0.161291 | 0.218870 | Supported by evidence | True |
| H4 | 60 | future directional market return | spearman_ic | 0.068166 | 0.000000 | 0.038170 | 0.095361 | Partially supported | True |
| H1 | 60 | top-quintile future realized volatility | auc_top_quintile | 0.750977 | 0.500000 | 0.732067 | 0.769378 | Supported by evidence | True |
| H2 | 60 | top-quintile future drawdown depth | auc_top_quintile | 0.653146 | 0.500000 | 0.632985 | 0.672759 | Supported by evidence | True |

## Interpretation

OPT-001 exceeds predefined null baselines most clearly for future realized volatility and future absolute movement. This is predictive validation only and does not evaluate trading or economic value.
