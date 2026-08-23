# OPT-001 / EV-001

# Risk Budget Analysis

Policy: `OPT001_RISK_BUDGET`

Benchmark: `STATIC_RISK_BUDGET`

Rule:

- LOW: 1.00 exposure
- MID: 0.75 exposure
- HIGH: 0.40 exposure

| use_case | policy | benchmark | policy_annualized_return | benchmark_annualized_return | delta_annualized_return | policy_annualized_volatility | benchmark_annualized_volatility | delta_annualized_volatility | policy_max_drawdown | benchmark_max_drawdown | delta_max_drawdown | policy_sortino | benchmark_sortino | delta_sortino | policy_calmar | benchmark_calmar | delta_calmar | policy_cvar_5pct_daily_return | benchmark_cvar_5pct_daily_return | delta_cvar_5pct_daily_return | policy_average_exposure | benchmark_average_exposure | delta_average_exposure | policy_final_equity_multiple | benchmark_final_equity_multiple | delta_final_equity_multiple | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-1 | OPT001_RISK_BUDGET | STATIC_RISK_BUDGET | 0.071559 | 0.073498 | -0.001939 | 0.121541 | 0.149865 | -0.028323 | -0.377249 | -0.417090 | 0.039841 | 0.818657 | 0.669442 | 0.149215 | 0.189686 | 0.176217 | 0.013470 | -0.018708 | -0.023149 | 0.004441 | 0.758906 | 0.750000 | 0.008906 | 3.443128 | 3.556319 | -0.113191 | Supported by evidence |

## Interpretation

This use case evaluates whether OPT-aware risk budgeting improves downside and volatility characteristics relative to a static risk budget. It does not evaluate alpha.
