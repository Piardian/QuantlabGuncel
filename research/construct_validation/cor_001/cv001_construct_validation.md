# COR-001 / CV-001: Construct Validation

## Purpose

Evaluate whether COR-001 behaves like a valid Market Correlation construct.

This study evaluates construct validity only.

It does not evaluate predictive validity, trading performance, alpha, profitability, or economic value.

## Construct Under Validation

COR-001 was frozen in CD-001 as:

```text
US Equity Market Average Pairwise Correlation State
```

Primary value:

```text
cor001_avg_pairwise_corr_60d
```

Definition:

Average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window.

## Data And Execution

The COR-001 implementation was run with the frozen configuration:

- start date: `2010-01-01`
- end date: `2025-12-31`
- universe: `sp500_current_universe.csv`
- total universe count: 503
- correlation window: 60 trading days
- normalization window: 252 valid observations
- minimum eligible count: 50

Output:

```text
output/cor001_correlation_state.csv
```

Output hash:

```text
d57b3b1baffaebb63becde64dc3984b991e8c07c17a629d9d04051eab898094e
```

## Data Quality Notes

Yahoo Finance reported missing or invalid data for:

- `BRK.B`
- `HONA`
- `BF.B`
- `FDXF`

The construct handled these through eligibility and coverage diagnostics.

## Validation Results

| Dimension | Evidence | Classification |
| --- | --- | --- |
| Internal consistency | Raw values are bounded within [-1, 1], percentile values are bounded within [0, 1], and output schema matches CD-001. | Supported by evidence |
| Coverage stability | Valid-date coverage averaged 93.15%; minimum valid-date coverage was 83.30%. | Supported by evidence |
| Distribution behavior | Raw average correlation spans from 0.0674 to 0.7301, showing meaningful variation across history. | Supported by evidence |
| Temporal behavior | Yearly averages vary materially across high and low co-movement periods. | Supported by evidence |
| Normalization behavior | 3,712 normalized observations were produced; percentile values remain bounded in [0, 1]. | Supported by evidence |
| Reproducibility | IM-001 deterministic verification passed; CV output hash is recorded. | Supported by evidence |

## Primary Findings

COR-001 produced:

- 4,023 total output rows
- 3,963 valid raw correlation observations
- 3,712 normalized observations
- first valid raw date: `2010-03-31`
- first normalized date: `2011-03-29`
- observed raw correlation range: 0.0674 to 0.7301
- mean raw correlation: 0.3140
- median raw correlation: 0.2983
- mean eligible security count: 468.55
- minimum eligible security count on valid dates: 419
- maximum eligible security count on valid dates: 498

## Construct Validity Assessment

COR-001 behaves consistently with the theoretical definition of a market-correlation construct:

- It measures cross-sectional co-movement.
- It is bounded and interpretable.
- It varies meaningfully across time.
- It reports eligibility, pair count, and coverage diagnostics.
- It produces normalized state values after the required warmup.

## Final CV-001 Conclusion

COR-001 is classified as:

```text
Supported by evidence
```

This conclusion is limited to construct validity.

No predictive, economic, alpha, profitability, trading-performance, or production-deployment conclusion is made.

