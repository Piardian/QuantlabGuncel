# Benchmark Comparison

Benchmark policies were predeclared as fixed exposure baselines. Dynamic MR-001 policies were compared only against their matched static counterparts.

 use_case                       policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  sortino  max_drawdown   calmar  win_rate  average_exposure  average_daily_turnover  5pct_daily_return  cvar_5pct_daily_return
Benchmark                 BUY_AND_HOLD   benchmark          4508          17.89      3.964112           0.093699               0.199820 0.729817     -0.523873 0.178859  0.547915          1.000000                0.000000          -0.018506               -0.030811
     UC-1           STATIC_RISK_BUDGET   benchmark          4508          17.89      3.225441           0.083894               0.174842 0.746789     -0.472439 0.177576  0.547915          0.875000                0.000000          -0.016193               -0.026959
     UC-2            STATIC_VOL_TARGET   benchmark          4508          17.89      2.556583           0.073503               0.149865 0.763341     -0.417090 0.176227  0.547915          0.750000                0.000000          -0.013880               -0.023108
     UC-3          STATIC_HEDGE_POLICY   benchmark          4508          17.89      1.960264           0.062546               0.124887 0.779463     -0.357740 0.174836  0.547915          0.625000                0.000000          -0.011566               -0.019257
     UC-1            MR001_RISK_BUDGET     dynamic          4508          17.89      4.266296           0.097318               0.164707 0.932533     -0.428948 0.226877  0.547915          0.932287                0.002828          -0.016496               -0.024983
     UC-2             MR001_VOL_TARGET     dynamic          4508          17.89      4.406695           0.098933               0.134114 1.180304     -0.322611 0.306664  0.547915          0.864574                0.005657          -0.014015               -0.020139
     UC-3       MR001_HEDGE_ACTIVATION     dynamic          4508          17.89      4.372182           0.098540               0.111815 1.409374     -0.217423 0.453218  0.547915          0.796861                0.008485          -0.011774               -0.017128
     UC-4 MR001_PORTFOLIO_RISK_CONTROL     dynamic          4508          17.89      4.166205           0.096142               0.103325 1.436603     -0.126008 0.762979  0.405723          0.729148                0.011313          -0.011212               -0.016632

use_case                       policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_average_exposure  delta_cvar_5pct_daily_return
    UC-1            MR001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.013425                    -0.010135            0.043491       0.185744      0.049301                0.057287                      0.001977
    UC-2             MR001_VOL_TARGET   STATIC_VOL_TARGET                 0.025431                    -0.015751            0.094479       0.416963      0.130437                0.114574                      0.002969
    UC-3       MR001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.035994                    -0.013073            0.140317       0.629911      0.278382                0.171861                      0.002129
    UC-4 MR001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                 0.002442                    -0.096495            0.397864       0.706786      0.584120               -0.270852                      0.014178
