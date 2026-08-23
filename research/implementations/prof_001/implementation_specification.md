# PROF-001 Implementation Specification

The implementation follows CD-001 exactly.

Input file:

`data/prof_001/accounting_statements.csv`

Required fields:

- security_id
- ticker
- fiscal_period_end
- revenue
- cost_of_goods_sold
- total_assets

Optional field:

- filing_date

Output:

- accounting_availability_date
- gross_profit
- gross_profitability
- prof001_state
- prof001_valid_observation
- exclusion_reason

The implementation aborts if the required dataset or required fields are unavailable.
