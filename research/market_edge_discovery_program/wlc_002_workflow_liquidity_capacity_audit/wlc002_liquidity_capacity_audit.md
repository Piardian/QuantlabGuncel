# WLC-002: Workflow Liquidity and Capacity Audit

## Purpose

Determine whether the UC-3 workflow has sufficient selected-name liquidity and capacity under predefined account-size and participation assumptions.

## Final Conclusion

**Liquidity Capacity Partially Supported**

## Evidence Classification

Supported by evidence:

- OHLCV volume data were obtained and selected-name dollar-volume features were calculated.
- Reference and OOS liquidity threshold pass rates were generated.
- Account-size participation feasibility was evaluated for $100k, $1M and $10M.

Conclusion-specific evidence:

- Reference $50M ADV20 pass rate: 0.8814
- OOS $50M ADV20 pass rate: 1.0000
- OOS 100k/1M 1% ADV20 pass check: True

Not supported:

- Production deployment.
- Broker-realistic execution.
- Live readiness.

## Outputs

- `liquidity_data_availability.csv`
- `selected_name_liquidity.csv`
- `liquidity_threshold_results.csv`
- `capacity_results.csv`
- `participation_limit_results.csv`
- `oos_liquidity_capacity_check.csv`
- `missing_data_report.csv`
