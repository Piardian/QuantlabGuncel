# Identity Remediation Open Limitations & Operational Constraints

1. **Registry Authoring**: Corporate action continuity events require authoritative verification from SEC filings / exchange notices before inclusion in `fuf001_identity_event_registry.csv`.
2. **Broker Data History**: When brokers do not backfill bars under successor tickers, multi-symbol historical querying is required.
3. **Execution Invariants Maintained**:
   - `TRADING_ENABLED = FALSE`
   - `PAPER_EXECUTION_ENABLED = FALSE`
   - `PAPER_T0 = NOT_ESTABLISHED`
   - `Scientific T0 = NOT_ESTABLISHED`
   - Broker mutation calls = 0
