# PAPER-001R Open Limitations

## PAPER-002 blockers

- The controller does not yet recompute current CSM/TSM signals from freshly acquired market data inside the Paper path.
- Data freshness is currently target-snapshot integrity, not per-symbol finalized daily-bar freshness.
- Scheduler is a calendar/session check inside the dry-run controller, not a durable monthly scheduling service.
- Duplicate order restart protection uses broker open-order reconciliation but not a durable local intent registry.

## Non-blocking limitations

- Broker mutation remains disabled.
- PAPER_T0 remains NOT_ESTABLISHED.
- Scientific T0 remains NOT_ESTABLISHED.

## Research/data limitations preserved

- Historical evidence remains NON_FORMAL.
- Current-universe bias remains HIGH.
- Survivorship/PIT quality remains PARTIAL.
- Corporate-actions limitation remains OPEN.
- Formal alpha validation has NOT occurred.
- Paper evidence would be prospective operational evidence only.
- Real-money trading remains unauthorized.
- Production remains unauthorized.
