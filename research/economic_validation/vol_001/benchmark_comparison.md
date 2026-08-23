# Benchmark Comparison

## Static Benchmarks

- Buy-and-Hold
- Static Risk Budget
- Static Volatility Target
- Static De-Risking Policy

## Dynamic Policies

- VOL001 Risk Budget
- VOL001 Vol Target
- VOL001 De-Risking
- VOL001 Portfolio Risk Control

## Results

use_case                        policy               benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.009782                    -0.009027            0.053021       0.212957      0.127211                      0.001332                0.066031
    UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.023049                     0.000198            0.020997       0.304032      0.131248                     -0.000076                0.150520
    UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.035550                     0.015808           -0.013586       0.294280      0.128297                     -0.002888                0.235008
    UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                -0.013381                    -0.049850            0.116057       0.337856      0.155587                      0.006962               -0.162047
