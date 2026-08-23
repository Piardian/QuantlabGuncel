# FUND-001 / EV-001

# Volatility Targeting Analysis

UC-2 evaluates whether a funding-stress-aware exposure ladder improves volatility management relative to static 0.75 exposure.

| use_case | policy | benchmark | delta_annualized_return | delta_annualized_volatility | delta_downside_volatility | delta_max_drawdown | delta_cvar_5pct_daily_return | delta_average_exposure | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-1 | UC1_FUND_RISK_BUDGET | STATIC_RISK_BUDGET_075 | 0.027782 | -0.000272 | -0.003132 | -0.063247 | 0.000001 | 0.056583 | Not supported |
| UC-2 | UC2_FUND_VOL_TARGET | STATIC_VOL_TARGET_075 | 0.017480 | -0.004550 | -0.006738 | -0.033602 | 0.000721 | 0.021352 | Not supported |
| UC-3 | UC3_FUND_HEDGE_ACTIVATION | STATIC_HEDGE_POLICY_075 | 0.034746 | 0.003804 | -0.000731 | -0.066685 | -0.000531 | 0.083557 | Not supported |
| UC-4 | UC4_FUND_PORTFOLIO_RISK_CONTROL | BUY_AND_HOLD | -0.004738 | -0.043528 | -0.039136 | -0.000905 | 0.006631 | -0.192528 | Not supported |

## Boundary

This is not an optimized volatility targeting model. It is a predefined exposure policy test.
