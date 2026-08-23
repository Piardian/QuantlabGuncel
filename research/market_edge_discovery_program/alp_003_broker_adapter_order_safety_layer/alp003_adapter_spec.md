# ALP-003 Adapter Specification

## Code

Adapter implementation:

`engine/alpaca_broker_adapter.py`

Test runner:

`scripts/alpaca_broker_adapter_tests.py`

## Architecture

```text
Strategy / Portfolio Layer
        ↓
Canonical Order Intent
        ↓
AlpacaBrokerAdapter
        ↓
DRY_RUN_ONLY
```

## Read Methods

- `get_account()`
- `get_positions()`
- `get_open_orders()`
- `get_asset(symbol)`
- `get_calendar(start, end)`

## Local Intent Methods

- `build_order_intent()`
- `validate_order_intent()`
- `generate_client_order_id()`
- `reconcile_positions()`
- `reconcile_orders()`

## Mutation Methods

The following methods exist only as disabled guards:

- `submit_order()`
- `replace_order()`
- `cancel_order()`

Each raises `BrokerMutationDisabled`.

