# Risk Budgeting Analysis

UC-1 compares a regime-aware 100% / 75% exposure ladder against a static 87.5% benchmark.

use_case             policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  sortino  max_drawdown   calmar  win_rate  average_exposure  average_daily_turnover  5pct_daily_return  cvar_5pct_daily_return
    UC-1 STATIC_RISK_BUDGET   benchmark          4508          17.89      3.225441           0.083894               0.174842 0.746789     -0.472439 0.177576  0.547915          0.875000                0.000000          -0.016193               -0.026959
    UC-1  MR001_RISK_BUDGET     dynamic          4508          17.89      4.266296           0.097318               0.164707 0.932533     -0.428948 0.226877  0.547915          0.932287                0.002828          -0.016496               -0.024983

use_case            policy          benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_average_exposure  delta_cvar_5pct_daily_return
    UC-1 MR001_RISK_BUDGET STATIC_RISK_BUDGET                 0.013425                    -0.010135            0.043491       0.185744      0.049301                0.057287                      0.001977

Classification: Supported by evidence
