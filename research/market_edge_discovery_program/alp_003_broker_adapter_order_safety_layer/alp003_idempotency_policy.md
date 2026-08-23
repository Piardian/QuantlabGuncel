# ALP-003 Idempotency Policy

## Result

`PASS`

## Rule

The adapter maintains a local set of known `client_order_id` values during validation.

If the same logical order appears again:

```text
DUPLICATE_CLIENT_ORDER_ID
↓
REJECTED_DUPLICATE
```

## Test Evidence

The duplicate synthetic intent test returned:

`REJECTED_DUPLICATE`

