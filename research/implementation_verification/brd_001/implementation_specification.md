# BRD-001 / IM-001: Implementation Specification

## Purpose

Document the implementation created for the frozen BRD-001 construct.

IM-001 evaluates implementation fidelity only.

It does not evaluate prediction, trading performance, alpha, profitability, or economic value.

## Frozen Construct

BRD-001 was frozen in CD-001 as:

```text
US Equity 200-Day Moving-Average Breadth State
```

Primary definition:

```text
brd001_pct_above_sma200_t =
    count(close_i,t > SMA200_i,t) / eligible_count_t
```

## Implementation Files

```text
research/constructs/brd_001/brd001_breadth_pipeline.py
research/constructs/brd_001/config.yaml
research/constructs/brd_001/verify_brd001.py
```

## Configuration

The implementation reads:

```text
research/constructs/brd_001/config.yaml
```

Frozen parameters:

| Parameter | Value |
| --- | ---: |
| `sma_window` | 200 |
| `normalization_window` | 252 |
| `minimum_eligible_count` | 50 |
| `universe_path` | `sp500_current_universe.csv` |

## Pipeline Components

The implementation provides:

- deterministic config loading
- deterministic universe loading and sorting
- Yahoo close-panel downloading
- optional CSV close-panel loading
- SMA200 calculation
- security-level above-SMA200 flags
- market-level breadth aggregation
- 252-day z-score normalization
- 252-day percentile normalization
- coverage diagnostics
- deterministic CSV serialization
- SHA-256 output hashing

## Output Schema

The output schema matches CD-001:

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

## Fidelity Assessment

The implementation is faithful to CD-001.

No construct formula, window, threshold, variable, or output was changed.

