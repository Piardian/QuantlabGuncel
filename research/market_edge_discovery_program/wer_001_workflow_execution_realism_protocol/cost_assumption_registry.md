# Cost Assumption Registry

WER-002 must use predefined cost assumptions only.

## Transaction Cost Scenarios

| Scenario | Round-trip cost |
|---|---:|
| Low | 0.05% |
| Medium | 0.10% |
| High | 0.25% |
| Stress | 0.50% |

These are research assumptions, not broker estimates.

## Slippage Scenarios

| Scenario | One-way slippage |
|---|---:|
| Low | 0.02% |
| Medium | 0.05% |
| High | 0.10% |
| Stress | 0.25% |

## Total Cost Treatment

Total assumed round-trip drag must include:

```text
round_trip_cost + 2 * one_way_slippage
```

No cost scenario may be changed after execution begins.
