# ALP-003 Failure Handling

## Result

`PASS`

## Rules

| Failure | Handling |
|---|---|
| timeout/network failure | bounded retry for reads |
| authentication loss | fail without secret leakage |
| malformed broker response | do not assume success |
| rate limit | bounded retry |
| unknown asset | reject intent |
| stale signal | reject intent |
| uncertain order state | reconcile before future submission |

## Core Principle

```text
uncertain state
↓
do not assume success
↓
do not duplicate
↓
reconcile first
```

