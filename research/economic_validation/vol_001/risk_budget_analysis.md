# Risk Budget Analysis

UC-1 compares `VOL001_RISK_BUDGET` against `STATIC_RISK_BUDGET`.

## Metrics

use_case             policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-1 STATIC_RISK_BUDGET   benchmark          3752          14.89      4.572218           0.122293               0.150467     -0.299884 1.265712 0.407802               -0.022984          0.875000                 0.00000
    UC-1 VOL001_RISK_BUDGET     dynamic          3752          14.89      5.340785           0.132075               0.141440     -0.246864 1.478670 0.535013               -0.021652          0.941031                 0.00613

## Comparison

use_case             policy          benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1 VOL001_RISK_BUDGET STATIC_RISK_BUDGET                 0.009782                    -0.009027            0.053021       0.212957      0.127211                      0.001332                0.066031
