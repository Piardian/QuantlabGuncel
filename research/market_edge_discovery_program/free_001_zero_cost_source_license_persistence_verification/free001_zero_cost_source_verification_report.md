# FREE-001 — Zero-Cost Source, License & Persistence Verification

## Program

Market Edge Discovery Program

## Purpose

FREE-001 evaluates whether a `$0/month` source stack can legally and technically support prospective, immutable, point-in-time and survivorship-aware US equity research.

This is not a performance study. It does not evaluate CSM, TSM, returns, Sharpe, drawdown, PnL or alpha.

## Starting State

| Item | State |
|---|---|
| OVA-001 | `OWNER_ACQUISITION_PARTIAL` |
| Paid vendor stack | `NONE` |
| Scientific T0 | `NOT_ESTABLISHED` |
| Alpha logic | `FROZEN` |
| Performance evaluation | `FORBIDDEN` |
| SLA-002 | `BLOCKED` |
| PDC-001 refreeze | `BLOCKED` |
| Production | `BLOCKED` |

## Candidate Free Stack Evaluated

| Source | Role | Result |
|---|---|---|
| Alpaca Basic/free access | market data, asset API, corporate actions | `FAILED_AUTH_REQUIRED` |
| Nasdaq Trader Symbol Directory | public symbol directory | `PARTIAL_PUBLIC_REFERENCE_SOURCE` |

## Actual Access Results

Nasdaq Trader public symbol-directory files were retrievable without authentication:

- `nasdaqlisted.txt`
- `otherlisted.txt`

Alpaca access was not verified because no credential/account evidence was available in the environment.

## Critical Finding

A zero-cost stack does not currently satisfy the minimum formal standard because:

- no authenticated free market-data source was verified
- no free daily OHLCV source was verified
- no explicit local persistence/license approval was established
- no zero-cost corporate-action source passed the minimum event requirement
- no stable security identifier system passed
- no source-backed storage dry run could be legally completed as formal evidence

## Final Decision

`FREE_DEVELOPMENT_ONLY`

## Interpretation

The free sources may support development, schema prototyping, symbol-directory ingestion tests and non-formal infrastructure testing.

They do not currently support formal prospective scientific evidence.

## Sources

- Alpaca market data page: https://alpaca.markets/data
- Alpaca corporate actions API documentation: https://docs.alpaca.markets/us/reference/corporateactions-1
- Alpaca disclosures and agreements: https://alpaca.markets/disclosures
- Nasdaq Trader Symbol Directory definitions: https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs
- Nasdaq Trader Symbol Lookup page: https://www.nasdaqtrader.com/trader.aspx?id=symbollookup
- Nasdaq Trader copyright and disclaimer: https://www.nasdaqtrader.com/trader.aspx?id=copydisclaimmain
- Nasdaq-listed file: https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt
- Other-listed file: https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt

