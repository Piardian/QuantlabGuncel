# EXB-002 Pipeline Smoke Test

## Scope

The smoke test executed only:

```text
historical data retrieval
TSM calculation
CSM calculation
CSM x TSM signal/interface construction
STOP BEFORE PORTFOLIO PERFORMANCE
```

## Results

| Metric | Value |
| --- | ---: |
| Input dates | 1,407 |
| Input symbols | 100 |
| TSM output rows | 140,700 |
| TSM valid observations | 53,080 |
| CSM x TSM interface rows | 140,700 |
| CSM x TSM selected-state count | 2,321 |
| Performance generated | NO |
| Broker mutation calls | 0 |

## Decision

PIPELINE_SMOKE_TEST = PASS
