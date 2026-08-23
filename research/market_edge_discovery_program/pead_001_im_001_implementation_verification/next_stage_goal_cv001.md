# PEAD-001 / CV-001 Construct Validation

Status:

**Not authorized yet**

CV-001 may begin only after a compliant point-in-time earnings event dataset is available at:

`data/pead_001/point_in_time_earnings_events.csv`

Required fields:

- security_id
- ticker
- announcement_date
- announcement_time_or_session
- fiscal_period_end
- actual_eps
- consensus_expected_eps
- consensus_timestamp
- price_reference

If the dataset is provided, CV-001 should validate construct coverage, exclusion rates, state distribution, timing safety, reproducibility and internal consistency.

Forbidden:

- Backtesting
- Future return prediction
- Profitability claims
- Unsafe revised estimates
