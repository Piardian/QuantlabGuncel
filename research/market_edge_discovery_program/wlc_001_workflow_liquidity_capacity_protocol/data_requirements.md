# Data Requirements

WLC-002 requires selected-name ticker-date liquidity data.

## Required Fields

| Field | Description |
|---|---|
| date | Trading date |
| ticker | Security identifier |
| adjusted_close | Adjusted close used by frozen CSM/TSM state generation |
| close | Raw close if available |
| volume | Daily share volume |
| dollar_volume | close multiplied by volume |
| adv20 | 20-trading-day average dollar volume |
| adv60 | 60-trading-day average dollar volume |

## Data Source Rules

Acceptable sources:

- Existing local OHLCV cache
- Deterministic public OHLCV download
- Previously validated project data source

Unacceptable sources:

- Manually edited ticker subsets
- Post-result universe filtering
- Look-ahead liquidity membership

## Missing Data Policy

If volume is missing for a selected name-date:

- record missingness
- do not impute silently
- exclude that observation only from liquidity/capacity calculations
- retain it in coverage reporting
