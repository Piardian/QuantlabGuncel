# FREE-001 Identifier Feasibility

## Decision

`PARTIAL`

## Evidence

Nasdaq Trader symbol-directory files expose ticker-like fields and exchange/listing information. They do not provide a verified permanent security identifier.

Alpaca may expose asset identifiers through authenticated APIs, but no authenticated access was available, so this could not be verified.

## Conservative Internal Policy Feasibility

A conservative internal `security_episode_id` could be created prospectively using:

- source name
- exchange
- ticker
- first-seen timestamp
- local snapshot ID

However, this is only a partial fallback. It cannot safely resolve ticker reuse, ticker changes, exchange transfers, relistings or mergers without additional evidence.

## Result

`IDENTITY_FEASIBILITY = PARTIAL`

Formal PDC cannot freeze identity policy from this evidence alone.

