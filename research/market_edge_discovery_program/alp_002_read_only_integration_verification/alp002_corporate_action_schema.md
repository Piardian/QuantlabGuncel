# ALP-002 Corporate Action Schema

Endpoint attempted: `GET /v2/corporate_actions`

Result: `NOT_ENTITLED / ENDPOINT_NOT_AVAILABLE`

Observed HTTP result: `HTTP_404`

## Interpretation

The Paper endpoint did not provide corporate-action records through the attempted route. This does not indicate failure of the core account/assets/calendar/bars/positions integration.

## Schema Status

`NOT_AVAILABLE`

## Limitation

Corporate-action read support remains unresolved for Alpaca Paper integration and must not be treated as validated.

