# ALP-002 Asset Schema

Endpoints:

- `GET /v2/assets`
- `GET /v2/assets/{symbol}`

Result: `PASS`

Observed fields:

| Field | Type | Nullable Observed |
|---|---|---|
| id | str | false |
| class | str | false |
| exchange | str | false |
| symbol | str | false |
| name | str | false |
| status | str | false |
| tradable | bool | false |
| marginable | bool | false |
| shortable | bool | false |
| easy_to_borrow | bool | false |
| fractionable | bool | false |
| attributes | list | false |
| borrow_status | str | false |

Observed active US equity asset list count: `14226`.

