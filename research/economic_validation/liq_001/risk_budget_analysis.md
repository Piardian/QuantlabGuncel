# Risk Budget Analysis

UC-1 compares `LIQ001_RISK_BUDGET` against `STATIC_RISK_BUDGET`.

## Metrics

use_case             policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-1 STATIC_RISK_BUDGET   benchmark          3752          14.89      3.408562           0.104775               0.150973     -0.303446 1.078497 0.345283               -0.023088          0.875000                0.000000
    UC-1 LIQ001_RISK_BUDGET     dynamic          3752          14.89      3.828332           0.111544               0.143485     -0.231730 1.228995 0.481353               -0.021757          0.941964                0.008396

## Comparison

use_case             policy          benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1 LIQ001_RISK_BUDGET STATIC_RISK_BUDGET                 0.006769                    -0.007488            0.071715       0.150498       0.13607                      0.001331                0.066964
