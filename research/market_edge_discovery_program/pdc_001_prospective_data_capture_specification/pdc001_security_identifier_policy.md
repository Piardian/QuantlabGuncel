# Security Identifier Policy

## Preferred Hierarchy

```text
source_permanent_security_id
  -> ticker
  -> source_company_id
  -> exchange
```

Ticker must not be the primary historical identity key.

## Internal ID Fallback

If no external immutable security ID is available, generate:

```text
internal_security_id = SHA256(source_name | first_seen_exchange | first_seen_ticker | first_seen_company_name | security_type | share_class | first_seen_timestamp)
```

This fallback is partial and must not merge separate share classes, ticker reuse cases, relistings or successor securities.

## Blocker

No source permanent security ID is currently verified.
