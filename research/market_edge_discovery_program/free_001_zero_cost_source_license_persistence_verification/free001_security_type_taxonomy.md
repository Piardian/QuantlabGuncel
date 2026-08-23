# FREE-001 Security-Type Taxonomy

## Nasdaq Trader Fields Observed

`nasdaqlisted.txt` first line:

```text
Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
```

`otherlisted.txt` first line:

```text
ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
```

## Taxonomy Assessment

| Security Type | Identifiable | Evidence |
|---|---|---|
| ETF | `YES` | ETF field exists |
| Test issue | `YES` | Test Issue field exists |
| Common stock | `PARTIAL` | Must infer from name/absence of ETF and other suffixes; not robust |
| REIT | `PARTIAL` | May appear in name but no dedicated field observed |
| ADR | `PARTIAL` | May appear in security name |
| Preferred stock | `PARTIAL` | May appear in security name |
| Warrants | `PARTIAL` | May appear in symbol/name |
| Rights | `PARTIAL` | May appear in symbol/name |
| Units | `PARTIAL` | May appear in symbol/name |
| SPAC | `PARTIAL` | May appear in name but no dedicated field observed |
| Multiple share classes | `PARTIAL` | May appear in symbol/name |

## Decision

`SECURITY_TYPE_TAXONOMY = PARTIAL`

The free symbol directory is not enough to freeze robust common-stock-only policy.

