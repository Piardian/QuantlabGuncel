# BRD-001 / CV-001: Construct Validation

## Purpose

Evaluate whether BRD-001 behaves like a valid Market Breadth construct.

This study evaluates construct validity only.

It does not evaluate predictive validity, trading performance, alpha, profitability, or economic value.

## Construct Under Validation

BRD-001 was frozen in CD-001 as:

```text
US Equity 200-Day Moving-Average Breadth State
```

Primary value:

```text
brd001_pct_above_sma200
```

Definition:

Percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above their own trailing 200-day simple moving average.

## Data and Execution

The BRD-001 implementation was run with the frozen configuration:

- start date: `2010-01-01`
- end date: `2025-12-31`
- universe: `sp500_current_universe.csv`
- total universe count: 503
- SMA window: 200
- normalization window: 252
- minimum eligible count: 50

Output:

```text
output/brd001_breadth_state.csv
```

Output hash:

```text
4de3a99bf5e49e2d5e942f2c8a58ee5ef193f006000edffa22f8f4413c338c82
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
| Internal consistency | Values are bounded within [0, 1], counts reconcile with eligible count, and output schema matches CD-001. | Supported by evidence |
| Coverage stability | Valid-date coverage averaged 92.94%; minimum valid-date coverage was 83.30%. | Supported by evidence |
| Distribution behavior | Breadth spans from 3.54% to 95.87%, showing meaningful variation across history. | Supported by evidence |
| Temporal behavior | Yearly averages vary materially across known broad-participation and narrow-participation periods. | Supported by evidence |
| Normalization behavior | 3,573 normalized observations were produced; percentile values remain bounded in [0, 1]. | Supported by evidence |
| Reproducibility | IM-001 deterministic verification passed; CV output hash is recorded. | Supported by evidence |

## Primary Findings

BRD-001 produced:

- 4,023 total output rows
- 3,824 valid raw breadth observations
- 3,573 normalized observations
- first valid raw date: `2010-10-18`
- first normalized date: `2011-10-14`
- observed breadth range: 0.0354 to 0.9587
- mean breadth: 0.6657
- median breadth: 0.7069

## Construct Validity Assessment

BRD-001 behaves consistently with the theoretical definition of market breadth:

- It measures cross-sectional participation.
- It is bounded and interpretable.
- It varies meaningfully across time.
- It distinguishes broad participation periods from weak participation periods.
- It reports coverage diagnostics required by CD-001.

## Final CV-001 Conclusion

BRD-001 is classified as:

```text
Supported by evidence
```

This conclusion is limited to construct validity.

No predictive, economic, alpha, profitability, trading-performance, or production-deployment conclusion is made.

