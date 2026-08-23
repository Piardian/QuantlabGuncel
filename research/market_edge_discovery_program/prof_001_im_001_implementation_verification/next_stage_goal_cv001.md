# PROF-001 / CV-001 Construct Validation

Status:

**Not authorized yet**

CV-001 may begin only after a compliant accounting statement dataset is available at:

`data/prof_001/accounting_statements.csv`

Required fields:

- security_id
- ticker
- fiscal_period_end
- revenue
- cost_of_goods_sold
- total_assets

Optional:

- filing_date

If the dataset is provided, CV-001 should validate construct coverage, exclusion rates, state distribution, publication-lag safety, reproducibility and internal consistency.

Forbidden:

- Backtesting
- Future return prediction
- Profitability claims
- Unsafe fiscal-period-end availability
