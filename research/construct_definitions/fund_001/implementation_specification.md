# FUND-001 / CD-001

# Implementation Specification

## Purpose

This file specifies how IM-001 must implement the frozen FUND-001 construct.

No implementation is performed in CD-001.

## Required Data Sources

Download from FRED:

- `DCPF3M`
- `DTB3`

## Required Processing Steps

1. Load both source series.
2. Parse dates as calendar dates.
3. Convert values to numeric percentage-point units.
4. Merge by exact date.
5. Mark rows with either missing input as `MISSING_INPUT`.
6. Compute raw spread only when both inputs are available.
7. Compute trailing 252-valid-observation z-score only when 252 valid historical spread observations exist.
8. Compute trailing 252-valid-observation percentile only when 252 valid historical spread observations exist.
9. Emit data quality flags.
10. Serialize deterministic output.

## No Forward Fill Rule

The implementation must not forward fill source values when computing the official construct.

Forward-filled diagnostic views may be created only as separate diagnostics and must not replace official construct values.

## Percentile Rule

Percentile rank must be computed using the current value relative to the trailing 252 valid spread observations including the current observation.

If ties exist, use average rank.

## Zero Standard Deviation Rule

If the trailing 252-observation standard deviation is zero, z-score must be missing and the data quality flag must include `ZERO_ROLLING_STD`.

## Expected Output Columns

- `date`
- `fund001_cp_rate`
- `fund001_tbill_rate`
- `fund001_cp_tbill_spread`
- `fund001_zscore_252d`
- `fund001_percentile_252d`
- `fund001_valid_observation_count_252d`
- `fund001_data_quality_flag`

## Determinism Requirements

Given identical input data, implementation must produce identical outputs.

No stochastic procedure is permitted.

## Verification Requirements For IM-001

IM-001 must verify:

- input loading,
- date alignment,
- missing-data behavior,
- raw spread formula,
- 252-valid-observation rolling calculations,
- percentile calculation,
- output schema,
- deterministic regeneration.

