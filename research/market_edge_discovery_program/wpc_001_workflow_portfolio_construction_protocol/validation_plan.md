# Validation Plan

## Study Name

WPC-002: Workflow Portfolio Construction Validation

## Required Analyses

1. Frozen input verification
2. Monthly rebalance calendar construction
3. Signal-date to entry-date mapping
4. Entry-date to exit-date mapping
5. Workflow holdings reconstruction
6. Benchmark holdings reconstruction
7. Gross portfolio return accounting
8. Position count analysis
9. Cash period analysis
10. Missing data analysis
11. Turnover measurement
12. Workflow versus benchmark gross comparison
13. Final portfolio construction classification

## Required Outputs

- `wpc002_portfolio_construction_validation.md`
- `rebalance_calendar.csv`
- `workflow_holdings.csv`
- `benchmark_holdings.csv`
- `portfolio_return_series.csv`
- `portfolio_accounting_checks.csv`
- `position_count_analysis.csv`
- `cash_period_analysis.csv`
- `turnover_analysis.csv`
- `missing_data_report.csv`
- `gross_benchmark_comparison.csv`
- `limitations.md`
- `executive_summary.md`
- `wpc002_manifest.json`

## Decision Categories

WPC-002 must conclude exactly one:

- Portfolio Construction Supported
- Portfolio Construction Partially Supported
- Portfolio Construction Not Supported
- Inconclusive

## Minimum Evidence Standard

Portfolio Construction Supported requires:

- deterministic rebalance calendar
- no look-ahead violations
- valid entry/exit mapping
- gross return accounting reproducible
- workflow and benchmark both constructed under identical timing

Partial support applies if construction works but material limitations remain.
