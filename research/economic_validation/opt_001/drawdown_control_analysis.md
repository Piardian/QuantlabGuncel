# OPT-001 / EV-001

# Drawdown Risk Control Analysis

Policy: `OPT001_DRAWDOWN_CONTROL`

Benchmark: `BUY_AND_HOLD`

Rule:

- LOW: 1.00 exposure
- MID: 0.80 exposure
- HIGH: 0.50 exposure

| use_case | policy | benchmark | policy_annualized_return | benchmark_annualized_return | delta_annualized_return | policy_annualized_volatility | benchmark_annualized_volatility | delta_annualized_volatility | policy_max_drawdown | benchmark_max_drawdown | delta_max_drawdown | policy_sortino | benchmark_sortino | delta_sortino | policy_calmar | benchmark_calmar | delta_calmar | policy_cvar_5pct_daily_return | benchmark_cvar_5pct_daily_return | delta_cvar_5pct_daily_return | policy_average_exposure | benchmark_average_exposure | delta_average_exposure | policy_final_equity_multiple | benchmark_final_equity_multiple | delta_final_equity_multiple | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-4 | OPT001_DRAWDOWN_CONTROL | BUY_AND_HOLD | 0.076251 | 0.093693 | -0.017442 | 0.133796 | 0.199819 | -0.066023 | -0.404733 | -0.523873 | 0.119139 | 0.795490 | 0.669442 | 0.126049 | 0.188399 | 0.178848 | 0.009551 | -0.020581 | -0.030865 | 0.010284 | 0.803438 | 1.000000 | -0.196562 | 3.723058 | 4.963623 | -1.240565 | Supported by evidence |

## Interpretation

This use case evaluates whether OPT-aware exposure reduction can improve drawdown and downside-risk characteristics relative to buy-and-hold. It does not evaluate alpha.
