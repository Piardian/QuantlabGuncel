# Security Identity & Corporate Action Resolution Policy v2

## 1. Purpose & Scope
This policy supersedes `fuf001_identity_policy.md` (v1) by establishing a deterministic, auditable, and immutable-compatible framework for resolving corporate actions, ticker changes, exchange transfers, and broker asset UUID changes in frozen exploratory universes.

## 2. Core Architectural Principles
1. **Universe Immutability**:
   - Frozen universe definitions (`fuf001_frozen_membership.csv`) are strictly read-only and canonically hashed (`BC7879B3...`).
   - No rows may be edited, added, or deleted in the frozen membership table.
2. **Operational Mapping Layer**:
   - Identity events and corporate actions are recorded in a version-controlled `fuf001_identity_event_registry.csv`.
   - Runtime resolution maps canonical member symbols to active market symbols and required historical query ranges without modifying strategy alpha code.
3. **Fail-Closed Safety**:
   - Any unverified ticker change, unresolved corporate action, or unexpected broker asset collision triggers an immediate guard block (`BLOCK_IDENTITY_MISMATCH`, `BLOCK_IDENTITY_CONTINUITY_UNRESOLVED`, `BLOCK_CORPORATE_ACTION_UNRESOLVED`, or `BLOCK_PRICE_SERIES_CONTINUITY`).

## 3. Continuity Classifications
- `UNCHANGED`: Active asset with matching broker identity and continuous single-symbol history.
- `VERIFIED_CONTINUITY`: Legally and economically continuous security with verified corporate action evidence (ticker change, exchange transfer, rebranding). Stitched across effective date boundaries.
- `VERIFIED_DISCONTINUITY`: Delisting, liquidation, or bankruptcy with no continuing equity security. Correctly marked as inactive without halting universe pipeline.
- `UNRESOLVED`: Unverified symbol change or missing audit trail. Must fail closed and block rebalance execution.

## 4. Historical Bar Stitching Rules
1. Pre-event series queried under `original_symbol` for dates <= effective_last_old_session.
2. Post-event series queried under `new_symbol` for dates >= effective_first_new_session.
3. Stitched frame must pass:
   - Old-symbol history reaches expected final old session.
   - New-symbol history begins at expected first new session.
   - Calendar continuity: no unexpected trading-session gaps between old and new sessions.
   - Zero date intersection between pre- and post-series.
   - Strictly monotonic date ordering with no duplicate dates.
   - All close prices finite and strictly greater than zero.
