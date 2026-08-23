# Portfolio Control Analysis

UC-4 compares `VOL001_PORTFOLIO_RISK_CONTROL` against `BUY_AND_HOLD`.

## Metrics

use_case                        policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino  calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-4 VOL001_PORTFOLIO_RISK_CONTROL     dynamic          3752          14.89      4.809496           0.125441               0.122112     -0.221116 1.595035 0.56731               -0.019305          0.837953                0.015458

## Comparison

use_case                        policy    benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-4 VOL001_PORTFOLIO_RISK_CONTROL BUY_AND_HOLD                -0.013381                     -0.04985            0.116057       0.337856      0.155587                      0.006962               -0.162047
