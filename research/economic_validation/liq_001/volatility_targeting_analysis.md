# Volatility Targeting Analysis

UC-2 compares `LIQ001_VOL_TARGET` against `STATIC_VOL_TARGET`.

## Metrics

use_case            policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-2 STATIC_VOL_TARGET   benchmark          3752          14.89      2.641945           0.090690               0.129406     -0.264421 1.089109 0.342977               -0.019790          0.750000                0.000000
    UC-2 LIQ001_VOL_TARGET     dynamic          3752          14.89      3.667723           0.109021               0.131332     -0.211113 1.316320 0.516413               -0.019913          0.902052                0.013593

## Comparison

use_case            policy         benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-2 LIQ001_VOL_TARGET STATIC_VOL_TARGET                 0.018331                     0.001926            0.053308       0.227211      0.173435                     -0.000122                0.152052
