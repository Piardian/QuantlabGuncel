# Identity Resolver Architecture & Call Graph

## 1. Execution Flow Diagram
```mermaid
flowchart TD
    A[PaperTradingController.run_dry_run] --> B[SecurityIdentityResolver.resolve_universe]
    B --> C{Registry Lookup}
    C -->|Unchanged| D[ResolvedIdentity: UNCHANGED]
    C -->|Verified Event| E[ResolvedIdentity: VERIFIED_CONTINUITY]
    C -->|Discontinued| F[ResolvedIdentity: VERIFIED_DISCONTINUITY]
    C -->|Unverified| G[ResolvedIdentity: UNRESOLVED -> FAIL CLOSED]
    
    B --> H[Collect data_symbols_required]
    H --> I[AlpacaBrokerAdapter.get_daily_bars]
    I --> J[SecurityIdentityResolver.stitch_price_series]
    
    J --> K{Stitch Validation}
    K -->|Overlap / Duplicate / Gap / Non-finite| L[BLOCK_PRICE_SERIES_CONTINUITY]
    K -->|Valid Monotonic| M[Logical Stitched Security History]
    
    M --> N[Pivot close_panel across 250 Canonical Members]
    N --> O[CSM-001 Transform]
    N --> P[TSM-001 Transform]
    O --> Q[Top Decile Selection]
    P --> Q
    Q --> R[PaperTradingController.build_order_intents]
    R --> S[OrderIntent with runtime_symbol & runtime_asset_id]
```

## 2. Module Responsibilities
- `engine.security_identity_resolver.SecurityIdentityResolver`: General deterministic resolution engine.
- `engine.paper_trading_controller.PaperTradingController`: Production controller coordinating resolution, data ingestion, alpha transformation, and safety checks.
