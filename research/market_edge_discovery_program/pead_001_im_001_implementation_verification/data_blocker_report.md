# Data Blocker Report

PEAD-001 requires external point-in-time earnings data.

Missing required dataset:

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

Without these fields, PEAD-001 cannot be validated without unacceptable look-ahead risk.
