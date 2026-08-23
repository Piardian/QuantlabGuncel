# Limitations

- CV-001 uses the IM-001 validation output, which loaded 59 symbols from a capped 60-symbol request.
- The universe is not survivorship-free.
- Yahoo Finance data may revise over time unless input snapshots are archived.
- LIQ-001 is an Amihud-style daily illiquidity proxy and does not measure bid-ask spread, order-book depth, immediacy, or resiliency.
- Warmup missing values are expected because the construct uses 20-day smoothing and 252-day z-score normalization.
- No predictive, alpha, profitability, economic, or production claim is made.
