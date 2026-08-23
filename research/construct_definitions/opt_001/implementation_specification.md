# OPT-001 / CD-001

# Implementation Specification

## Purpose

This file specifies how IM-001 must implement the frozen OPT-001 construct.

No implementation is performed in CD-001.

## Required Data Source

Download from FRED:

- `VIXCLS`

## Required Processing Steps

1. Load source series.
2. Parse dates as calendar dates.
3. Convert values to numeric index-point units.
4. Treat missing or non-positive values as invalid raw observations.
5. Do not forward fill official construct values.
6. Compute trailing 252-valid-observation z-score only when 252 valid historical observations exist.
7. Compute trailing 252-valid-observation percentile only when 252 valid historical observations exist.
8. Emit data quality flags.
9. Serialize deterministic output.

## Percentile Rule

Percentile rank must be computed using the current value relative to the trailing 252 valid VIX observations including the current observation.

If ties exist, use average rank.

## Zero Standard Deviation Rule

If the trailing 252-observation standard deviation is zero, z-score must be missing and the data quality flag must include `ZERO_ROLLING_STD`.

## Expected Output Columns

- `date`
- `opt001_vix_close`
- `opt001_zscore_252d`
- `opt001_percentile_252d`
- `opt001_valid_observation_count_252d`
- `opt001_data_quality_flag`

## Determinism Requirements

Given identical input data, implementation must produce identical outputs.

No stochastic procedure is permitted.

