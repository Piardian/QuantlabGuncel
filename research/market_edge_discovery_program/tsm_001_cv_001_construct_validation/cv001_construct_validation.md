# TSM-001 / CV-001 Construct Validation

## Purpose

Evaluate whether the implemented TSM-001 construct behaves as a stable, reproducible and internally consistent implementation of frozen CD-001 on real data.

No future returns, alpha, trading performance, strategy backtest, volatility scaling or economic value were evaluated.

## Frozen Construct

TSM-001 is the Raw 12-1 Time-Series Momentum State:

```text
tsm_return_12_1 = adjusted_close_t_minus_21 / adjusted_close_t_minus_252 - 1
state = POSITIVE if return > 0; NEGATIVE if return < 0; NEUTRAL if return = 0
```

## Data Scope

- Source close panel: `output/csm_001_cv001/adjusted_close_panel.csv`
- Close panel dates: 2010-01-04 to 2025-12-30
- Close panel tickers: 503
- Valid construct dates: 2011-01-03 to 2025-12-30
- Construct state rows: 2,023,569
- Valid observations: 1,768,840

## Validation Results

- Average coverage ratio: 0.8741
- Minimum coverage ratio, including required warmup: 0.0000
- Minimum coverage ratio after valid observations begin: 0.8370
- Positive state rate: 0.7228
- Negative state rate: 0.2772
- Neutral state rate: 0.000072
- 21-day median state agreement: 0.8923
- 63-day median state agreement: 0.8057
- Deterministic reproducibility: PASSED

## Final CV-001 Classification

**Partially supported**

The implementation is reproducible and internally coherent under the available real-data panel. The classification is not stronger than Partially Supported because the source panel is current-constituent based rather than survivorship-free historical membership.
