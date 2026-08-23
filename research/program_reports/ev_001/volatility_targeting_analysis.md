# Volatility Targeting Analysis

UC-2 compares a regime-aware 100% / 50% exposure ladder against a static 75% benchmark.

use_case            policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  sortino  max_drawdown   calmar  win_rate  average_exposure  average_daily_turnover  5pct_daily_return  cvar_5pct_daily_return
    UC-2 STATIC_VOL_TARGET   benchmark          4508          17.89      2.556583           0.073503               0.149865 0.763341     -0.417090 0.176227  0.547915          0.750000                0.000000          -0.013880               -0.023108
    UC-2  MR001_VOL_TARGET     dynamic          4508          17.89      4.406695           0.098933               0.134114 1.180304     -0.322611 0.306664  0.547915          0.864574                0.005657          -0.014015               -0.020139

use_case           policy         benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_average_exposure  delta_cvar_5pct_daily_return
    UC-2 MR001_VOL_TARGET STATIC_VOL_TARGET                 0.025431                    -0.015751            0.094479       0.416963      0.130437                0.114574                      0.002969

Classification: Supported by evidence
