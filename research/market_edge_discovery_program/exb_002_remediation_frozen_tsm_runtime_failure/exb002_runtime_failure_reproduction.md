# EXB-002 Runtime Failure Reproduction

## Failure Reproduced

FAILURE_REPRODUCED = YES

## Original Failure

Exception type:

```text
IndexError
```

Exception message:

```text
pop index out of range
```

Stack trace location:

```text
research/implementations/tsm_001/feature_pipeline.py
```

Failing function:

```text
TSM001FeaturePipeline.build_features
```

Failing operation:

```text
direction_score.replace({1.0: "POSITIVE", 0.0: "NEUTRAL", -1.0: "NEGATIVE"})
```

## Failing Runtime Input

Input source:

```text
EXB-001 frozen Alpaca IEX daily reduced dataset specification
```

Observed smoke input shape after retrieval:

```text
dates = 1407
symbols = 100
```

## Performance Blackout

No return, PnL, CAGR, Sharpe, drawdown, benchmark, or portfolio performance metric was generated during reproduction.
