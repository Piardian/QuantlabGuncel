# EXB-002 TSM Golden Test

## Golden Test Result

TSM_GOLDEN_TEST = PASS

## Synthetic Case

A 253-row business-day price series was constructed:

```text
GOLD = 100, 101, 102, ..., 352
```

## Manual Reference

For the first valid observation:

```text
expected_return_12_1 = price_t_minus_21 / price_t_minus_252 - 1
expected_return_12_1 = 331 / 100 - 1
expected_return_12_1 = 2.31
expected_state = POSITIVE
```

## Implementation Output

```text
observed_return_12_1 = 2.31
observed_state = POSITIVE
```

## Decision

The implementation output matches the frozen mathematical specification.
