# FREE-001 Corporate Action Assessment

## Decision

`FAIL`

## Minimum Required Events

| Event | Free Stack Status |
|---|---|
| Stock split | `NOT_VERIFIED` |
| Reverse split | `NOT_VERIFIED` |
| Cash dividend | `NOT_VERIFIED` |
| Ticker change | `PARTIAL_SYMBOL_DIRECTORY_ONLY` |

## Evidence

Alpaca publicly documents a corporate-actions endpoint, but authenticated access was not available.

Nasdaq Trader symbol-directory files can show current symbol listings and some changes through directory-related files, but they do not satisfy full corporate-action event semantics.

## Result

`CORPORATE_ACTION_CAPABILITY = FAIL`

The free stack cannot pass formal PDC without explicit corporate-action event coverage or a predefined limited acceptable standard.

