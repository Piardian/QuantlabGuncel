# FUND-001 / PV-001

# Cross-Period Validation

20-day horizon cross-period information coefficients:

| hypothesis | target | period | observations | spearman_ic |
| --- | --- | --- | --- | --- |
| H1 | future_realized_vol | 1998_2004 | 0 |  |
| H1 | future_realized_vol | 2005_2012 | 743 | 0.448161 |
| H1 | future_realized_vol | 2013_2020 | 1893 | 0.198602 |
| H1 | future_realized_vol | 2021_2026 | 787 | 0.279074 |
| H2 | future_drawdown_risk | 1998_2004 | 0 |  |
| H2 | future_drawdown_risk | 2005_2012 | 743 | 0.227813 |
| H2 | future_drawdown_risk | 2013_2020 | 1893 | 0.155633 |
| H2 | future_drawdown_risk | 2021_2026 | 787 | 0.166566 |
| H3 | future_liq_stress | 1998_2004 | 0 |  |
| H3 | future_liq_stress | 2005_2012 | 476 | 0.512893 |
| H3 | future_liq_stress | 2013_2020 | 1893 | 0.323295 |
| H3 | future_liq_stress | 2021_2026 | 787 | 0.341937 |
| H4 | future_credit_stress | 1998_2004 | 0 |  |
| H4 | future_credit_stress | 2005_2012 | 0 |  |
| H4 | future_credit_stress | 2013_2020 | 0 |  |
| H4 | future_credit_stress | 2021_2026 | 252 | -0.211126 |

## Interpretation

Cross-period stability is strongest for volatility, drawdown risk, and liquidity stress. Credit-stress validation is limited to the latest period because of short CRD-001 overlap.
