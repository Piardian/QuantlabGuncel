# Implementation Specification

IM-001 implements the frozen LIQ-001 construct exactly as specified in CD-001.

## Components

- `feature_pipeline.py` computes security-level and aggregate liquidity features.
- `liq001_liquidity_model.py` wraps the frozen aggregate model.
- `liquidity_inference.py` provides reusable inference helpers.
- `validate_liq_001.py` runs an end-to-end structural validation.
- `config.yaml` stores deterministic execution settings.
- `tests/test_liq001.py` verifies core formula behavior and determinism.

## Frozen Formula

```text
illiquidity_i,t = abs(log_return_i,t) / dollar_volume_i,t
aggregate_illiquidity_t = median_i(illiquidity_i,t)
liq001_illiquidity_20d_t = rolling_mean(aggregate_illiquidity_t, 20)
liq001_zscore_t = rolling_zscore(liq001_illiquidity_20d_t, 252)
```

## Output Columns

- `date`
- `aggregate_illiquidity`
- `liq001_illiquidity_20d`
- `liq001_zscore`
- `eligible_count`
- `coverage_ratio`

## Scope Boundary

This implementation does not evaluate prediction, trading performance, alpha, or economic utility.

