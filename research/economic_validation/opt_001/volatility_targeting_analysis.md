# OPT-001 / EV-001

# Volatility Targeting Analysis

Policy: `OPT001_VOL_TARGET`

Benchmark: `STATIC_VOL_TARGET`

Rule:

- Static target: 10 percent annualized volatility.
- OPT-aware target: LOW 12 percent, MID 10 percent, HIGH 6 percent.
- Exposure is clipped between 0.0 and 1.5.

| use_case | policy | benchmark | policy_annualized_return | benchmark_annualized_return | delta_annualized_return | policy_annualized_volatility | benchmark_annualized_volatility | delta_annualized_volatility | policy_max_drawdown | benchmark_max_drawdown | delta_max_drawdown | policy_sortino | benchmark_sortino | delta_sortino | policy_calmar | benchmark_calmar | delta_calmar | policy_cvar_5pct_daily_return | benchmark_cvar_5pct_daily_return | delta_cvar_5pct_daily_return | policy_average_exposure | benchmark_average_exposure | delta_average_exposure | policy_final_equity_multiple | benchmark_final_equity_multiple | delta_final_equity_multiple | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-2 | OPT001_VOL_TARGET | STATIC_VOL_TARGET | 0.067927 | 0.072022 | -0.004096 | 0.105557 | 0.110378 | -0.004822 | -0.200392 | -0.203207 | 0.002814 | 0.857640 | 0.882005 | -0.024366 | 0.338968 | 0.354429 | -0.015461 | -0.016463 | -0.017071 | 0.000608 | 0.802807 | 0.797229 | 0.005578 | 3.240217 | 3.469872 | -0.229655 | Partially supported |

## Interpretation

This use case evaluates whether OPT-001 adds economic utility to a predefined volatility-targeting workflow. It does not evaluate trading edge or strategy profitability.
