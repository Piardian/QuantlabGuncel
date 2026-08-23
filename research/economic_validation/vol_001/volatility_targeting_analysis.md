# Volatility Targeting Analysis

UC-2 compares `VOL001_VOL_TARGET` against `STATIC_VOL_TARGET`.

## Metrics

use_case            policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-2 STATIC_VOL_TARGET   benchmark          3752          14.89      3.451177           0.105489               0.128971     -0.261218 1.273752 0.403834               -0.019701           0.75000                0.000000
    UC-2 VOL001_VOL_TARGET     dynamic          3752          14.89      5.052101           0.128538               0.129169     -0.240221 1.577784 0.535082               -0.019776           0.90052                0.009995

## Comparison

use_case            policy         benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-2 VOL001_VOL_TARGET STATIC_VOL_TARGET                 0.023049                     0.000198            0.020997       0.304032      0.131248                     -0.000076                 0.15052
