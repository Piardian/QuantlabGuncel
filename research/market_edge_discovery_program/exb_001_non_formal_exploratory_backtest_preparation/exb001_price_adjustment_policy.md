# EXB-001 Price Adjustment Policy

## Frozen Policy

EXB-001 and the authorized EXB-002 exploratory run must use:

- Feed: iex
- Timeframe: 1Day
- Adjustment: raw

## Rationale

The policy follows the verified accessible Alpaca data path and avoids introducing unverified corporate-action processing.

## Restrictions

- No alternative adjustment mode may be selected after observing exploratory results.
- No split/dividend repair may be introduced inside EXB-002.
- If corporate-action-aware adjustment becomes required, a new data-source validation gate must be opened before formal use.

## Known Consequence

Raw prices may be distorted by splits, dividends, mergers, ticker changes, or other corporate actions. This is a major limitation and prevents formal production-grade inference.
