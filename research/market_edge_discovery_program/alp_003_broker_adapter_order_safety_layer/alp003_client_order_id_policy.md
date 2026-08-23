# ALP-003 Client Order ID Policy

## Result

`PASS`

## Policy

Deterministic `client_order_id` is generated from:

- `strategy_id`
- `rebalance_id`
- `symbol`
- `side`
- `sequence`

Example:

```text
CSMXTSM-20260831-AAPL-BUY-001
```

## Requirements

| Requirement | Status |
|---|---|
| Deterministic | `PASS` |
| Reproducible | `PASS` |
| Unique per logical order | `PASS` |
| Bounded length | `PASS` |
| No randomness | `PASS` |
| No secrets | `PASS` |
| No performance data | `PASS` |

