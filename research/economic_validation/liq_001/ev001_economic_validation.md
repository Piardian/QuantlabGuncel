# LIQ-001 / EV-001: Economic Validation

## Purpose

Evaluate whether LIQ-001 provides measurable economic value inside predefined liquidity-aware risk-management workflows.

This stage evaluates economic utility only. It does not claim alpha or universal superiority.

## Overall Classification

**Partially supported**

## Use-Case Classifications

use_case                        policy        classification
    UC-1            LIQ001_RISK_BUDGET   Partially supported
    UC-2             LIQ001_VOL_TARGET   Partially supported
    UC-3       LIQ001_HEDGE_ACTIVATION   Partially supported
    UC-4 LIQ001_PORTFOLIO_RISK_CONTROL Supported by evidence

## Benchmark Comparison

use_case                        policy           benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1            LIQ001_RISK_BUDGET  STATIC_RISK_BUDGET                 0.006769                    -0.007488            0.071715       0.150498      0.136070                      0.001331                0.066964
    UC-2             LIQ001_VOL_TARGET   STATIC_VOL_TARGET                 0.018331                     0.001926            0.053308       0.227211      0.173435                     -0.000122                0.152052
    UC-3       LIQ001_HEDGE_ACTIVATION STATIC_HEDGE_POLICY                 0.029224                     0.017494            0.005755       0.221754      0.142910                     -0.002904                0.237140
    UC-4 LIQ001_PORTFOLIO_RISK_CONTROL        BUY_AND_HOLD                -0.009533                    -0.048509            0.118159       0.299162      0.141450                      0.007011               -0.159648

## Interpretation

LIQ-001 provides measurable economic utility primarily through risk reduction, volatility management, and downside-risk control.

The evidence is strongest where liquidity stress is used to reduce exposure during elevated liquidity-risk states. This is not an alpha claim.
