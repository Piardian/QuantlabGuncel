# EV-001: MR-001 Economic Validation

## Scope
MR-001 is evaluated only as a risk-forecasting construct inside predefined risk-management workflows.

## Primary Result
use_case                       policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_average_exposure  delta_cvar_5pct_daily_return
    UC-1            MR001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.013425                    -0.010135            0.043491       0.185744      0.049301                0.057287                      0.001977
    UC-2             MR001_VOL_TARGET   STATIC_VOL_TARGET                 0.025431                    -0.015751            0.094479       0.416963      0.130437                0.114574                      0.002969
    UC-3       MR001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.035994                    -0.013073            0.140317       0.629911      0.278382                0.171861                      0.002129
    UC-4 MR001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                 0.002442                    -0.096495            0.397864       0.706786      0.584120               -0.270852                      0.014178

## Use-Case Classifications
- UC-1: Supported by evidence
- UC-2: Supported by evidence
- UC-3: Supported by evidence
- UC-4: Partially supported

## Interpretation
Economic value is assessed only as risk reduction, volatility management, hedge activation efficiency, and downside-risk control. No alpha claim is made.
