# EXB-002 Determinism Test

## Test

The repaired TSM component was executed twice using identical frozen EXB-001 input retrieval specification.

## Results

| Metric | Value |
| --- | ---: |
| TSM rows | 140,700 |
| TSM valid observations | 53,080 |
| TSM positive observations | 24,979 |
| Reproducibility | PASS |

## Decision

TSM_REPRODUCIBILITY = PASS

Identical input produced identical output hash.
