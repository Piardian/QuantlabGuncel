# ALP-002 Historical Daily Bar Schema

Endpoint: `GET /v2/stocks/bars`

Result: `PASS`

Test labels:

- `NON_FORMAL_INTEGRATION_TEST_DATA`
- `Scientific T0 = NOT_ESTABLISHED`

Observed fields:

| Field | Meaning | Type | Nullable Observed |
|---|---|---|---|
| t | timestamp | str | false |
| o | open | float | false |
| h | high | float | false |
| l | low | float | false |
| c | close | float | false |
| v | volume | int | false |
| n | trade count | int | false |
| vw | VWAP | float | false |

Observed bar count: `10`.

No returns, rankings, signals or performance statistics were calculated.

