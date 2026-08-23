# Robustness Analysis

## Period Results

   period use_case                        policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
2011_2014     UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.007708                    -0.003318            0.016847       0.159875      0.121648                      0.001253                0.078141
2015_2019     UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                -0.001766                    -0.001660           -0.000290      -0.019222     -0.010651                      0.000236                0.057035
2020_2022     UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.013359                    -0.033209            0.071715       0.183134      0.109746                      0.005679                0.024471
2023_2025     UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.013686                     0.015246           -0.021759      -0.072866     -0.056388                     -0.001863                0.111684
2011_2014     UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.021398                     0.005568            0.020073       0.278774      0.272052                     -0.000184                0.173506
2015_2019     UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.006625                     0.005035            0.009296       0.024892      0.075871                     -0.000778                0.131558
2020_2022     UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.017563                    -0.026953            0.053308       0.232861      0.127825                      0.003929                0.083995
2023_2025     UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.036300                     0.032237           -0.043971      -0.067749     -0.064795                     -0.003871                0.226698
2011_2014     UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.034528                     0.019412            0.018425       0.310933      0.445500                     -0.002424                0.268870
2015_2019     UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.014633                     0.016077           -0.013326       0.012286      0.058213                     -0.002772                0.206081
2020_2022     UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.020059                    -0.007152            0.005755       0.204200      0.096797                     -0.000348                0.143519
2023_2025     UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.058529                     0.050218           -0.066644      -0.088799     -0.074181                     -0.006299                0.341711
2011_2014     UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                -0.006960                    -0.039867            0.097369       0.412065      0.584619                      0.006482               -0.118541
2015_2019     UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                -0.013300                    -0.036310            0.056914       0.142661      0.095402                      0.005459               -0.201908
2020_2022     UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                 0.002783                    -0.102861            0.118159       0.232585      0.097036                      0.014177               -0.261905
2023_2025     UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                -0.020285                    -0.007879            0.001445      -0.071518     -0.098878                      0.001639               -0.039947

## Interpretation

Robustness is assessed across fixed historical periods. The purpose is stability of risk utility, not optimization.
