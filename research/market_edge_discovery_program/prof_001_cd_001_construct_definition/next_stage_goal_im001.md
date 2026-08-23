# PROF-001 / IM-001 Implementation Development & Verification

Purpose: implement the frozen PROF-001 Conservative-Lag Gross Profitability State.

IM-001 must first verify whether required accounting data exists.

Required:

- security_id
- ticker
- fiscal_period_end
- revenue
- cost_of_goods_sold
- total_assets
- filing_date if available
- trading calendar

If required data is unavailable, IM-001 must conclude:

**Implementation incomplete / blocked by missing accounting statement data**

Forbidden:

- Using fiscal period end as availability date.
- Using restated data without limitation reporting.
- Backtesting.
- Profitability claims.
- Parameter optimization.
