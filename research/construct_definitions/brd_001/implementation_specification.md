# BRD-001 / CD-001: Implementation Specification

## Purpose

Specify exactly what IM-001 must implement.

## Required Module

IM-001 should create a deterministic BRD-001 implementation module.

Suggested files:

```text
research/constructs/brd_001/breadth_pipeline.py
research/constructs/brd_001/config.yaml
```

Exact paths may differ if consistent with repository conventions.

## Input Universe

The implementation must read:

```text
sp500_current_universe.csv
```

The file must contain a `ticker` column.

The loaded ticker list must be sorted deterministically before processing.

## Input Data

For each ticker, daily adjusted or normalized close must be available.

The implementation must document the data source and adjustment basis.

## Required Calculation

For each ticker:

```text
sma200_i,t = rolling_mean(close_i,t, 200)
above_sma200_i,t = close_i,t > sma200_i,t
```

For each date:

```text
brd001_pct_above_sma200_t =
    count(above_sma200_i,t == True) / eligible_count_t
```

## Required Normalization

For each valid market date:

```text
brd001_zscore_t =
    (brd001_pct_above_sma200_t - rolling_mean_252)
    / rolling_std_252
```

```text
brd001_percentile_t =
    count(trailing_252_values <= current_value) / 252
```

## Required Outputs

The implementation must produce a daily CSV containing:

- `date`
- `brd001_pct_above_sma200`
- `brd001_zscore`
- `brd001_percentile`
- `brd001_count_above_sma200`
- `brd001_count_not_above_sma200`
- `brd001_eligible_count`
- `brd001_total_universe_count`
- `brd001_coverage_ratio`
- `brd001_valid_observation`

## Required Verification

IM-001 must verify:

- universe loading
- close data loading
- SMA200 calculation
- eligibility rules
- market-level aggregation
- normalization
- output serialization
- deterministic re-run hash

## Forbidden During IM-001

IM-001 must not:

- change the construct formula
- change the moving-average length
- change the normalization window
- add predictive tests
- run trading strategies
- evaluate returns
- optimize thresholds

