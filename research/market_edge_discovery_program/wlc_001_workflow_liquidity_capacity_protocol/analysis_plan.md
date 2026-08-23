# Analysis Plan

## Study Name

WLC-002: Workflow Liquidity and Capacity Audit

## Required Analyses

1. Frozen input verification
2. OHLCV data availability check
3. UC-3 selected-name reconstruction
4. Dollar-volume feature calculation
5. Liquidity threshold pass-rate analysis
6. Account-size capacity analysis
7. Participation-limit analysis
8. OOS liquidity/capacity check
9. Missing-data analysis
10. Final liquidity/capacity classification

## Required Outputs

- `wlc002_liquidity_capacity_audit.md`
- `liquidity_data_availability.csv`
- `selected_name_liquidity.csv`
- `liquidity_threshold_results.csv`
- `capacity_results.csv`
- `participation_limit_results.csv`
- `oos_liquidity_capacity_check.csv`
- `missing_data_report.csv`
- `limitations.md`
- `executive_summary.md`
- `wlc002_manifest.json`

## Decision Categories

WLC-002 must conclude exactly one:

- Liquidity Capacity Supported
- Liquidity Capacity Partially Supported
- Liquidity Capacity Not Supported
- Inconclusive

## Minimum Evidence Standard

Liquidity Capacity Supported requires:

- Most selected UC-3 observations pass at least the $50 million ADV threshold.
- $100,000 and $1,000,000 account sizes remain below 1% ADV for most selected observations.
- OOS liquidity evidence does not contradict reference evidence.

Liquidity Capacity Partially Supported requires:

- Smaller account sizes appear feasible, but larger account sizes or stricter thresholds remain constrained.

Liquidity Capacity Not Supported requires:

- Liquidity and participation constraints block the workflow under predefined assumptions.

Inconclusive requires:

- Reliable selected-name volume data are unavailable or coverage is insufficient.
