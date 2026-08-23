# Hedge Activation Analysis

UC-3 compares a regime-aware 100% / 25% exposure ladder against a static 62.5% benchmark.

use_case                 policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  sortino  max_drawdown   calmar  win_rate  average_exposure  average_daily_turnover  5pct_daily_return  cvar_5pct_daily_return
    UC-3    STATIC_HEDGE_POLICY   benchmark          4508          17.89      1.960264           0.062546               0.124887 0.779463     -0.357740 0.174836  0.547915          0.625000                0.000000          -0.011566               -0.019257
    UC-3 MR001_HEDGE_ACTIVATION     dynamic          4508          17.89      4.372182           0.098540               0.111815 1.409374     -0.217423 0.453218  0.547915          0.796861                0.008485          -0.011774               -0.017128

use_case                 policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_average_exposure  delta_cvar_5pct_daily_return
    UC-3 MR001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.035994                    -0.013073            0.140317       0.629911      0.278382                0.171861                      0.002129

Classification: Supported by evidence
