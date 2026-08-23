# Implementation Specification

## Required Input

A fixed US equity universe with daily OHLCV data.

For each ticker:

- date
- close
- volume

## Processing Steps

1. Load daily close and volume for every universe security.
2. Sort data by ticker and date.
3. Compute daily log return:

```text
log_return_i,t = ln(close_i,t / close_i,t-1)
```

4. Compute daily dollar volume:

```text
dollar_volume_i,t = close_i,t * volume_i,t
```

5. Mark a security-day eligible if:

```text
close_i,t > 0
volume_i,t > 0
previous_close_i,t exists
dollar_volume_i,t > 0
log_return_i,t is finite
```

6. Compute security-level illiquidity:

```text
illiquidity_i,t = abs(log_return_i,t) / dollar_volume_i,t
```

7. For each date, compute:

```text
aggregate_illiquidity_t = median(illiquidity_i,t across eligible securities)
eligible_count_t = number of eligible securities
coverage_ratio_t = eligible_count_t / universe_size
```

8. Keep dates where:

```text
eligible_count_t >= 50
```

9. Compute:

```text
liq001_illiquidity_20d_t = rolling_mean(aggregate_illiquidity_t, 20)
liq001_zscore_t = rolling_zscore(liq001_illiquidity_20d_t, 252)
```

10. Serialize outputs to CSV.

## Required Output Columns

- `date`
- `aggregate_illiquidity`
- `liq001_illiquidity_20d`
- `liq001_zscore`
- `eligible_count`
- `coverage_ratio`

## Determinism Requirements

- Same input data must produce identical output.
- Universe list must be fixed before execution.
- Missing data rules must be deterministic.
- No random initialization is permitted.

## Forbidden in Implementation

- No threshold tuning.
- No predictive labels.
- No return outcome columns.
- No strategy backtest integration.

