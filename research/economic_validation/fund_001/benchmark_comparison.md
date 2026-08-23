# FUND-001 / EV-001

# Benchmark Comparison

| use_case | policy | benchmark | delta_annualized_return | delta_annualized_volatility | delta_downside_volatility | delta_max_drawdown | delta_cvar_5pct_daily_return | delta_average_exposure | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-1 | UC1_FUND_RISK_BUDGET | STATIC_RISK_BUDGET_075 | 0.027782 | -0.000272 | -0.003132 | -0.063247 | 0.000001 | 0.056583 | Not supported |
| UC-2 | UC2_FUND_VOL_TARGET | STATIC_VOL_TARGET_075 | 0.017480 | -0.004550 | -0.006738 | -0.033602 | 0.000721 | 0.021352 | Not supported |
| UC-3 | UC3_FUND_HEDGE_ACTIVATION | STATIC_HEDGE_POLICY_075 | 0.034746 | 0.003804 | -0.000731 | -0.066685 | -0.000531 | 0.083557 | Not supported |
| UC-4 | UC4_FUND_PORTFOLIO_RISK_CONTROL | BUY_AND_HOLD | -0.004738 | -0.043528 | -0.039136 | -0.000905 | 0.006631 | -0.192528 | Not supported |

## Full Policy Metrics

| use_case | policy | policy_type | annualized_return | annualized_volatility | downside_volatility | max_drawdown | sortino | calmar | average_exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Benchmark | BUY_AND_HOLD | benchmark | 0.150829 | 0.171170 | 0.140667 | -0.291098 | 1.103407 | 0.518138 | 1.000000 |
| UC-1 | STATIC_RISK_BUDGET_075 | benchmark | 0.114192 | 0.128377 | 0.105500 | -0.223617 | 1.103407 | 0.510662 | 0.750000 |
| UC-1 | UC1_FUND_RISK_BUDGET | dynamic | 0.141975 | 0.128105 | 0.102368 | -0.286864 | 1.377487 | 0.494920 | 0.806583 |
| UC-2 | STATIC_VOL_TARGET_075 | benchmark | 0.114192 | 0.128377 | 0.105500 | -0.223617 | 1.103407 | 0.510662 | 0.750000 |
| UC-2 | UC2_FUND_VOL_TARGET | dynamic | 0.131672 | 0.123827 | 0.098762 | -0.257218 | 1.330495 | 0.511909 | 0.771352 |
| UC-3 | STATIC_HEDGE_POLICY_075 | benchmark | 0.114192 | 0.128377 | 0.105500 | -0.223617 | 1.103407 | 0.510662 | 0.750000 |
| UC-3 | UC3_FUND_HEDGE_ACTIVATION | dynamic | 0.148939 | 0.132182 | 0.104769 | -0.290302 | 1.409008 | 0.513048 | 0.833557 |
| UC-4 | UC4_FUND_PORTFOLIO_RISK_CONTROL | dynamic | 0.146091 | 0.127641 | 0.101530 | -0.292003 | 1.423687 | 0.500306 | 0.807472 |
