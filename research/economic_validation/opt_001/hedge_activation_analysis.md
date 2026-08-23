# OPT-001 / EV-001

# Hedge Activation Analysis

Policy: `OPT001_DYNAMIC_HEDGE`

Benchmark: `STATIC_HEDGE_POLICY`

Rule:

- LOW/MID: 1.00 net equity exposure
- HIGH: 0.50 net equity exposure

This is a simplified hedge-equivalent exposure model, not an options execution simulation.

| use_case | policy | benchmark | policy_annualized_return | benchmark_annualized_return | delta_annualized_return | policy_annualized_volatility | benchmark_annualized_volatility | delta_annualized_volatility | policy_max_drawdown | benchmark_max_drawdown | delta_max_drawdown | policy_sortino | benchmark_sortino | delta_sortino | policy_calmar | benchmark_calmar | delta_calmar | policy_cvar_5pct_daily_return | benchmark_cvar_5pct_daily_return | delta_cvar_5pct_daily_return | policy_average_exposure | benchmark_average_exposure | delta_average_exposure | policy_final_equity_multiple | benchmark_final_equity_multiple | delta_final_equity_multiple | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-3 | OPT001_DYNAMIC_HEDGE | STATIC_HEDGE_POLICY | 0.084625 | 0.077723 | 0.006902 | 0.151683 | 0.159856 | -0.008173 | -0.460589 | -0.439705 | -0.020883 | 0.786827 | 0.669442 | 0.117385 | 0.183732 | 0.176762 | 0.006970 | -0.023422 | -0.024692 | 0.001270 | 0.907831 | 0.800000 | 0.107831 | 4.276734 | 3.815208 | 0.461527 | Partially supported |

## Interpretation

This use case evaluates whether high OPT states can support a predefined hedge activation workflow. It does not evaluate hedge instrument implementation, option pricing, or live execution.
