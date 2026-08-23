# ALP-003 Order Validation Policy

## Result

`PASS`

## Validation Checks

- symbol format
- asset exists
- asset active
- asset tradable
- side is buy/sell
- quantity or notional exists
- quantity positive and finite
- notional positive and finite
- reference price positive and finite
- order type supported
- time in force supported
- no duplicate `client_order_id`
- market session eligible
- intent not stale
- broker mode is `DRY_RUN`
- trading is not enabled

## Rejected Test Cases

- duplicate intent
- zero quantity
- negative quantity
- unknown symbol
- non-tradable asset
- stale intent
- market closed
- malformed side

