# Hedge Activation Analysis

UC-3 compares `LIQ001_HEDGE_ACTIVATION` against `STATIC_HEDGE_POLICY`.

## Metrics

use_case                  policy policy_type  observations  years_covered  total_return  annualized_return  annualized_volatility  max_drawdown  sortino   calmar  cvar_5pct_daily_return  average_exposure  average_daily_turnover
    UC-3     STATIC_HEDGE_POLICY   benchmark          3752          14.89      1.987699           0.076281               0.107838     -0.223963 1.099275 0.340596               -0.016492           0.62500                 0.00000
    UC-3 LIQ001_HEDGE_ACTIVATION     dynamic          3752          14.89      3.452158           0.105505               0.125332     -0.218208 1.321029 0.483506               -0.019395           0.86214                 0.01879

## Comparison

use_case                  policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-3 LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.029224                     0.017494            0.005755       0.221754       0.14291                     -0.002904                 0.23714
