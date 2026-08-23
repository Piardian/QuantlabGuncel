# DSA-001 Data Source Acquisition

## Final Decision

`PARTIAL_SOURCE_APPROVED`

## Interpretation

A scientifically credible institutional source stack exists for the required data problems, but the repository does not currently contain licensed local datasets or sample schemas sufficient to authorize BFL-002.

The strongest candidate stack is:

```text
CRSP US Stock Databases
+ Compustat Point in Time / Preliminary History / Unrestated Quarterly
+ CRSP/Compustat Merged Database (CCM)
+ I/B/E/S Detail/Summary History
+ GICS History
```

This stack is scientifically acceptable in principle for PIT/survivorship-aware US equity research if licensed and schema-validated.

A more accessible commercial partial alternative is:

```text
Sharadar / Nasdaq Data Link / QuantRocket stack
```

This may support partial US equity, S&P 500 constituent, fundamentals, delisted-price, and event research, but it does not fully replace institutional IBES expectation timing or CRSP/Compustat permanent identifier lineage without further validation.

## Why Not SOURCE_APPROVED?

No candidate dataset is currently available locally.

No local schema has been inspected for the institutional stack.

Licensing/access has not been confirmed.

Therefore BFL-002 remains unauthorized.

## Why Not SOURCE_UNAVAILABLE?

Credible institutional and commercial source families exist with documented PIT, inactive/delisted, fundamental, forecast, and historical classification capabilities.

The blocker is acquisition/access/schema validation, not absence of any scientifically acceptable source family.
