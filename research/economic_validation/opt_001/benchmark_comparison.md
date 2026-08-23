# OPT-001 / EV-001

# Benchmark Comparison

| use_case | policy | benchmark | delta_annualized_return | delta_annualized_volatility | delta_max_drawdown | delta_sortino | delta_calmar | delta_cvar_5pct_daily_return | delta_average_exposure | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-1 | OPT001_RISK_BUDGET | STATIC_RISK_BUDGET | -0.001939 | -0.028323 | 0.039841 | 0.149215 | 0.013470 | 0.004441 | 0.008906 | Supported by evidence |
| UC-2 | OPT001_VOL_TARGET | STATIC_VOL_TARGET | -0.004096 | -0.004822 | 0.002814 | -0.024366 | -0.015461 | 0.000608 | 0.005578 | Partially supported |
| UC-3 | OPT001_DYNAMIC_HEDGE | STATIC_HEDGE_POLICY | 0.006902 | -0.008173 | -0.020883 | 0.117385 | 0.006970 | 0.001270 | 0.107831 | Partially supported |
| UC-4 | OPT001_DRAWDOWN_CONTROL | BUY_AND_HOLD | -0.017442 | -0.066023 | 0.119139 | 0.126049 | 0.009551 | 0.010284 | -0.196562 | Supported by evidence |

## Interpretation

Each use case is compared only against its predefined benchmark. No claim is generalized beyond these workflows.
