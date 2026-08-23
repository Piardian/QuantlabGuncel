# Market Data Schema

Minimum fields:

- trade_date
- security_id
- ticker
- exchange
- raw_open
- raw_high
- raw_low
- raw_close
- raw_volume
- vendor_adjusted_close if available
- source_timestamp
- ingestion_timestamp
- schema_version
- freshness_status
- capture_provenance

Optional fields:

- VWAP
- trade_count
- bid
- ask
- shares_outstanding

Blocker:

Raw market data source is unresolved.
