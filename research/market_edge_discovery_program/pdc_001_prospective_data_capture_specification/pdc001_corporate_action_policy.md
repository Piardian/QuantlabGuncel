# Corporate Action Policy

Corporate actions must be stored as events, not only embedded into adjusted prices.

Required event fields:

- event_id
- security_id
- event_type
- announcement_date where available
- ex_date
- record_date where available
- effective_date
- payment_date where applicable
- adjustment_factor where applicable
- source_timestamp
- ingestion_timestamp
- source

Events covered:

- stock splits
- reverse splits
- cash dividends
- stock dividends
- rights issues
- spin-offs
- mergers
- acquisitions
- symbol changes
- share-class changes

Blocker:

Corporate-action source is unresolved.
