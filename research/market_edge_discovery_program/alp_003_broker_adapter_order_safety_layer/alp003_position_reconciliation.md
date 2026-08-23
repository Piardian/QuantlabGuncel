# ALP-003 Position Reconciliation

## Result

`PASS`

## States

- `MATCH`
- `MISSING_INTERNAL`
- `MISSING_BROKER`
- `QUANTITY_MISMATCH`
- `SYMBOL_MISMATCH`
- `UNKNOWN`

## Test Evidence

| Test | Result |
|---|---|
| synthetic match | `MATCH` |
| synthetic mismatch | `QUANTITY_MISMATCH` |
| zero-position account | handled as empty match state |

No positions were created during ALP-003.

