# Remaining Operational Risks

## PAPER-002 blockers

- No complete CSM-001 x TSM-001 Paper controller was found.
- No real readiness CLI was found.
- No real scheduler was found.
- No executable data freshness guard was found.
- No executable incident-handling module was found.
- No integrated Paper dry-run path was found.
- Strategy hash guard lacks a frozen expected hash and contains DUMMYHASH in T0 spec.
- Artifact integrity is not valid because final hashes are DUMMY.
- Duplicate symbol input can break target portfolio weight integrity.
- Duplicate order protection is in-memory unless reconciled against broker state by an integrated controller.
- Risk guards exist as a standalone manager but are not connected to a real Paper execution path.

## Non-blocking Paper limitations

- Alpaca corporate-actions endpoint limitation remains open from ALP-002.
- The known credential exposure incident remains a security limitation until keys are rotated.

## Research/data limitations

- Historical evidence remains NON_FORMAL.
- Current-universe bias remains HIGH.
- Survivorship/PIT quality remains PARTIAL.
- Formal alpha validation has NOT occurred.
- PAPER evidence would be prospective operational evidence, not proof of formal alpha.

## Future production-only requirements

- Real-money trading remains unauthorized.
- Production remains unauthorized.
- Execution, capacity, slippage, monitoring, rollback, and operator controls would require separate gates.
