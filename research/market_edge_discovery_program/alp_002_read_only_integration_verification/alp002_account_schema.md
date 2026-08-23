# ALP-002 Account Schema

Endpoint: `GET /v2/account`

Result: `PASS`

Observed selected fields:

| Field | Type | Nullable Observed |
|---|---|---|
| id | str | false |
| account_number | str | false |
| status | str | false |
| currency | str | false |
| buying_power | str | false |
| cash | str | false |
| equity | str | false |
| portfolio_value | str | false |
| trading_blocked | bool | false |
| transfers_blocked | bool | false |
| account_blocked | bool | false |
| created_at | str | false |

Numeric financial values are returned as strings by the API and must be parsed explicitly by later components.

