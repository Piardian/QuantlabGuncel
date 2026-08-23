# Construct Specification

Construct:

**PROF-001 Conservative-Lag Gross Profitability State**

Unit of observation:

Firm fiscal-period accounting observation.

Primary variable:

`gross_profitability`

Formula:

```text
(revenue - cost_of_goods_sold) / total_assets
```

State output:

```text
PROFITABLE / UNPROFITABLE / NEUTRAL / INVALID
```

Decision-time safety:

The observation is not available until after filing date or, if filing date is unavailable, 180 calendar days after fiscal period end.
