# ALP-003 Dry-Run Policy

## Result

`PASS`

## Required Mode

```text
BROKER_MODE = DRY_RUN
```

## Allowed

- read broker state
- build payloads
- validate intents
- reconcile positions/orders
- write audit logs

## Blocked

- order submission
- order replacement
- order cancellation
- position close

## Evidence

Broker mutation calls:

`0`

