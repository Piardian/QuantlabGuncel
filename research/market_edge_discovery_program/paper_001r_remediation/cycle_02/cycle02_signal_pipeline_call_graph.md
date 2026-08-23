# PAPER-001R Cycle 2 Signal Pipeline Call Graph

```text
PaperTradingController.run_dry_run
  -> load_membership
     -> FUF001 frozen membership CSV
  -> load_calendar
     -> AlpacaBrokerAdapter.get_calendar (read-only)
  -> latest_completed_session
     -> determines signal_as_of_session from completed Alpaca calendar close
  -> build_current_signal_target
     -> fetch_daily_bars
        -> AlpacaBrokerAdapter.get_daily_bars (read-only, batched)
     -> parse_bar_payload
     -> duplicate/future-bar/freshness/history checks
     -> import_frozen_models
        -> research/implementations/csm_001/CSM001MomentumModel
        -> research/implementations/tsm_001/TSM001MomentumModel
     -> CSM top-decile candidate gate
     -> TSM positive-state gate
     -> equal-weight current target portfolio
     -> write_signal_snapshot (audit output only)
  -> AlpacaBrokerAdapter.get_positions (read-only)
  -> AlpacaBrokerAdapter.get_open_orders (read-only)
  -> AlpacaBrokerAdapter.get_account (read-only)
  -> reconcile_positions
  -> build_order_intents (local intent objects only)
  -> reconcile_orders
  -> validate_order_intent
  -> PaperSafetyManager.check_risk_guards
  -> PaperSafetyManager.check_buying_power
  -> execution_flags_authorize
  -> DRY_RUN_BLOCK_EXECUTION_FLAGS_FALSE
```

No EXB-003 target snapshot is used as production target input. Snapshot target loading remains only as an explicit regression fixture path when `target_path` is provided.
