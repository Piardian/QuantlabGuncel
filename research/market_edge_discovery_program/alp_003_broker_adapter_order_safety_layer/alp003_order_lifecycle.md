# ALP-003 Order Lifecycle

## ALP-003 Lifecycle

```text
CREATED
↓
VALIDATED
↓
BROKER_ELIGIBLE
↓
SUBMISSION_BLOCKED_ALP003
```

## Future Lifecycle Not Reached In ALP-003

- `SUBMITTED`
- `ACKNOWLEDGED`
- `PARTIALLY_FILLED`
- `FILLED`
- `REJECTED`
- `CANCELED`

## Result

`PASS`

Valid test intents correctly stopped at:

`SUBMISSION_BLOCKED_ALP003`

