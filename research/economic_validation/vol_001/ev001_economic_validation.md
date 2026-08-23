# VOL-001 / EV-001: Economic Validation

## Purpose

Evaluate whether VOL-001 provides measurable economic value inside predefined volatility-aware risk-management workflows.

This stage evaluates economic utility only. It does not claim alpha or universal superiority.

## Predefined Policies

- Normal volatility state: `vol001_zscore <= 1`
- Elevated volatility state: `1 < vol001_zscore <= 2`
- Severe volatility state: `vol001_zscore > 2`

The exposure ladders were fixed before execution.

## Overall Classification

**Partially supported**

## Use-Case Classifications

use_case                        policy        classification
    UC-1            VOL001_RISK_BUDGET Supported by evidence
    UC-2             VOL001_VOL_TARGET   Partially supported
    UC-3              VOL001_DERISKING         Not supported
    UC-4 VOL001_PORTFOLIO_RISK_CONTROL Supported by evidence

## Benchmark Comparison

use_case                        policy               benchmark  delta_annualized_return  delta_annualized_volatility  delta_max_drawdown  delta_sortino  delta_calmar  delta_cvar_5pct_daily_return  delta_average_exposure
    UC-1            VOL001_RISK_BUDGET      STATIC_RISK_BUDGET                 0.009782                    -0.009027            0.053021       0.212957      0.127211                      0.001332                0.066031
    UC-2             VOL001_VOL_TARGET       STATIC_VOL_TARGET                 0.023049                     0.000198            0.020997       0.304032      0.131248                     -0.000076                0.150520
    UC-3              VOL001_DERISKING STATIC_DERISKING_POLICY                 0.035550                     0.015808           -0.013586       0.294280      0.128297                     -0.002888                0.235008
    UC-4 VOL001_PORTFOLIO_RISK_CONTROL            BUY_AND_HOLD                -0.013381                    -0.049850            0.116057       0.337856      0.155587                      0.006962               -0.162047

## Interpretation

VOL-001 provides measurable economic utility primarily through volatility and drawdown reduction when used as a risk-control sensor.

This is not an alpha claim. It is an economic utility assessment for predefined risk-management workflows only.
