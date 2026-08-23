# ALP-002 Timestamp Semantics

## Result

`PASS`

## Observed

| Resource | Timestamp Semantics |
|---|---|
| Account | `created_at` returned as string timestamp |
| Calendar | `date`, `open`, `close`, `session_open`, `session_close` returned as date/time strings |
| Historical bars | `t` returned as timestamp string |
| Integration execution | recorded as UTC timestamp |

## Required Later Handling

Later stages must explicitly parse:

- Alpaca bar timestamps as API-provided timestamp strings
- calendar times as exchange-session time semantics
- ingestion timestamps separately from source timestamps

No silent timezone conversion is authorized.

