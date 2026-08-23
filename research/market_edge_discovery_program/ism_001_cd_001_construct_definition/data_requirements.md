# Data Requirements

Required data:

- Ken French 49 Industry Portfolios monthly value-weighted returns.

Expected implementation input:

```text
data/ism_001/ken_french_49_industry_value_weighted_monthly.csv
```

Required fields after parsing:

- `month`
- 49 industry return columns

Returns must be converted from percent units to decimal units if the source file uses percentages.

No individual security price data is required for ISM-001 CD-001.

