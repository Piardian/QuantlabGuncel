# PAPER-001R Real Call Graph

Intended PAPER-002 path status: `PARTIAL`.

The repository now has one executable dry-run path, but it does not yet recompute live/current CSM and TSM signals from newly acquired market bars. It consumes the frozen EXB-003 target snapshot and validates it through the Paper controller.

```text
scripts/paper_end_to_end_dry_run.py::main
-> engine.paper_trading_controller.PaperTradingController.run_dry_run
-> PaperSafetyManager.verify_environment
-> PaperSafetyManager.verify_universe_hash
-> PaperSafetyManager.verify_strategy_hash
-> PaperTradingController.load_membership
-> PaperTradingController.load_target_frame
-> PaperTradingController.validate_target_frame
-> AlpacaBrokerAdapter.from_environment
-> AlpacaBrokerAdapter.get_calendar
-> AlpacaBrokerAdapter.get_positions
-> AlpacaBrokerAdapter.get_open_orders
-> AlpacaBrokerAdapter.get_account
-> AlpacaBrokerAdapter.reconcile_positions
-> AlpacaBrokerAdapter.reconcile_orders
-> PaperTradingController.build_order_intents
-> AlpacaBrokerAdapter.validate_order_intent
-> PaperSafetyManager.check_risk_guards
-> PaperSafetyManager.check_buying_power
-> PaperAuditTrail.append
-> PaperIncidentLog.append when needed
-> submission boundary
-> DRY_RUN_BLOCK_EXECUTION_FLAGS_FALSE
```

Broker mutation boundary:

```text
AlpacaBrokerAdapter.submit_order
AlpacaBrokerAdapter.replace_order
AlpacaBrokerAdapter.cancel_order
```

All mutation methods remain disabled and are not called by the controller.

Remaining gap:

```text
market-data acquisition
-> current data freshness by member
-> CSM001MomentumModel.transform
-> TSM001MomentumModel.transform
-> target portfolio
```

This live/current signal-generation section is not yet connected inside the controller.
