# Benchmark Comparison

## Static Benchmarks

- Buy-and-Hold
- Static Risk Budget
- Static Volatility Target
- Static Hedge Policy

## Dynamic Policies

- LIQ001 Risk Budget
- LIQ001 Vol Target
- LIQ001 Hedge Activation
- LIQ001 Portfolio Risk Control

## Results

use_case                        policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.006769                    -0.007488            0.071715       0.150498      0.136070                      0.001331                0.066964
    UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.018331                     0.001926            0.053308       0.227211      0.173435                     -0.000122                0.152052
    UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.029224                     0.017494            0.005755       0.221754      0.142910                     -0.002904                0.237140
    UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                -0.009533                    -0.048509            0.118159       0.299162      0.141450                      0.007011               -0.159648
