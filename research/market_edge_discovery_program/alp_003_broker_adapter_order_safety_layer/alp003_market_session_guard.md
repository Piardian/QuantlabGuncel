# ALP-003 Market Session Guard

## Result

`PASS`

## Policy

The adapter distinguishes:

- `MARKET_OPEN`
- `MARKET_CLOSED`
- `HOLIDAY`
- `PRE_OPEN`
- `POST_CLOSE`
- `UNKNOWN`

## Test Evidence

A synthetic market-closed intent returned:

`REJECTED_MARKET_SESSION`

No local clock-only assumption is used as the final market-open policy.

