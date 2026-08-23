# Portfolio Control Analysis

UC-4 compares `LIQ001_PORTFOLIO_RISK_CONTROL` against `BUY_AND_HOLD`.

## Metrics

use_case                        policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-4 LIQ001_PORTFOLIO_RISK_CONTROL     dynamic          3752          14.89      3.665272           0.108982               0.124032     -0.222889 1.366604 0.488953               -0.019376          0.840352                0.020789

## Comparison

use_case                        policy    benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-4 LIQ001_PORTFOLIO_RISK_CONTROL BUY_AND_HOLD                -0.009533                    -0.048509            0.118159       0.299162       0.14145                      0.007011               -0.159648
