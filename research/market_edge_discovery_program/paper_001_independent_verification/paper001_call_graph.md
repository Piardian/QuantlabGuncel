# PAPER-001 Independent Call Graph

## Verified components

```text
ALP-003 broker adapter tests
-> AlpacaBrokerAdapter.from_environment
-> AlpacaReadOnlyTransport.get_json
-> get_account / get_positions / get_open_orders / get_asset / get_calendar
-> build_order_intent
-> validate_order_intent
-> reconcile_positions / reconcile_orders
-> submit_order / replace_order / cancel_order boundary raises BrokerMutationDisabled
```

This path is real and executable, but it is not the full CSM x TSM Paper pipeline.

## Frozen research target path

```text
scripts/exb003_prepare_frozen_250.py
-> load frozen FUF membership
-> verify canonical FUF universe hash
-> fetch Alpaca bars
-> CSM001MomentumModel.transform
-> TSM001MomentumModel.transform
-> merge CSM/TSM state
-> target_portfolios
-> exb003_target_portfolio_instructions.csv
```

This path verifies frozen strategy compatibility and target construction for research preparation. It is not a live Paper controller.

## Missing expected Paper path

Expected but not found:

```text
paper execution entry point
-> load PAPER config
-> verify fail-closed flags
-> load frozen universe
-> verify universe hash
-> verify strategy hash
-> fetch/read latest market data
-> freshness guard
-> eligibility guard
-> CSM
-> TSM
-> target portfolio
-> read Alpaca account/positions/orders
-> position reconciliation
-> order reconciliation
-> build order intents from deltas
-> risk guards
-> buying power guard
-> audit trail / incident handling
-> submission boundary
```

Audit conclusion: `PARTIAL`.

One real executable path connecting the complete PAPER-001 system was not found. Current evidence consists of disconnected components: ALP-003 adapter tests, `PaperSafetyManager` unit tests, and EXB-003 target-generation research code.
