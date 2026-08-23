# CSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether the implemented CSM-001 construct behaves as a stable, reproducible and internally consistent implementation of the frozen CD-001 definition.

No returns, alpha, trading performance, Sharpe, CAGR, drawdown or economic value were evaluated.

## Frozen Construct

CSM-001 is the Canonical 12-1 Cross-Sectional Momentum State.

For each security and date:

```text
return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1
momentum_score = cross-sectional percentile rank of return_12_1
top_decile_flag = momentum_score >= 0.90
```

## Data Scope

- Universe file: `sp500_current_universe.csv`
- Configured tickers: 503
- Downloaded close columns: 503
- Failed / unavailable tickers: 2
- Close panel dates: 2010-01-04 to 2025-12-30
- Valid construct dates: 2011-01-03 to 2025-12-30
- Construct state rows: 2,023,569
- Valid observations: 1,768,841

## Validation Results

- Average coverage ratio: 0.8741
- Minimum coverage ratio, including required warmup: 0.0000
- Minimum coverage ratio after valid observations begin: 0.8370
- Average top-decile selection rate among valid rows: 0.1010
- Rank monotonicity status: PASSED
- Deterministic reproducibility: PASSED

## Final CV-001 Classification

**Partially supported**

The implementation is reproducible and internally coherent under the available data sample. The classification is not stronger than Partially Supported because the universe is current S&P 500 membership rather than survivorship-free historical membership, and Yahoo data availability varies by ticker.
