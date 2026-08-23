# Cross-Period Validation

## Purpose

Evaluate whether COR-001 predictive relationships remain directionally consistent across fixed historical blocks.

## Periods

The study used four fixed blocks:

- 2011-2014
- 2015-2018
- 2019-2022
- 2023-2025

## Direction Consistency

| Hypothesis | 20d Direction Consistency | 60d Direction Consistency |
| --- | ---: | ---: |
| H1 Future realized volatility | 4 / 4 | 4 / 4 |
| H2 Future drawdown risk | 3 / 4 | 1 / 4 |
| H3 Future breadth deterioration | 4 / 4 | 4 / 4 |
| H4 Future correlation persistence | 4 / 4 | 4 / 4 |

## Interpretation

Supported by evidence:

Future realized volatility, future breadth deterioration, and future correlation persistence show stable direction across periods.

Partially supported:

Future drawdown risk is not stable across periods, especially at the 60-day horizon.

## Data File

Detailed period-level results are stored in:

```text
research/predictive_validation/cor_001/cross_period_validation.csv
```

