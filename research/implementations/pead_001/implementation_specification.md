# PEAD-001 Implementation Specification

The implementation follows CD-001 exactly.

Input file:

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

Output:

- standardized_earnings_surprise
- pead_state
- first_valid_decision_timestamp
- pead001_valid_observation
- exclusion_reason

The implementation aborts if the required dataset or required fields are unavailable.
