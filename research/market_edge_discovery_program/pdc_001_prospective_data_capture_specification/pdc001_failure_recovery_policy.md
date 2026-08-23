# Failure, Recovery And Replay Policy

Capture states:

- SUCCESS
- PARTIAL_SUCCESS
- FAILED
- RETRY_PENDING
- MANUAL_REVIEW

Recovery provenance:

- LIVE_CAPTURE
- VERIFIED_REPLAY
- LATE_RETRIEVAL
- UNVERIFIED_BACKFILL

`UNVERIFIED_BACKFILL` must not enter the formal prospective research dataset.

Failed manifests must be preserved and never replaced.
