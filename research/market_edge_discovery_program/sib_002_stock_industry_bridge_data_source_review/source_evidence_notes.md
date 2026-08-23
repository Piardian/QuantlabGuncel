# Source Evidence Notes

## Ken French 49 Industry Portfolios

Kenneth French documents that 49 industry portfolios assign NYSE, AMEX and NASDAQ stocks to industry portfolios using four-digit SIC codes at the end of June of year `t`.

The documented construction uses Compustat SIC codes for fiscal year ending in calendar year `t-1`, and CRSP SIC codes for June of year `t` when Compustat SIC is unavailable.

Interpretation:

- This is the most direct scientific compatibility target for ISM-001.
- It implies that a valid stock-to-ISM bridge should be SIC-based if the objective is compatibility with Ken French 49 industry states.

## CRSP / Compustat Historical SIC

CRSP/WRDS documentation references historical identifiers, tickers, CUSIPs, SIC codes, name histories and delisting-related security histories.

Interpretation:

- This is the most plausible source family for point-in-time historical stock-level mapping.
- Access, schema and coverage must be verified before implementation.

## GICS History

S&P Global describes GICS History as active and inactive classifications for companies with history from 1985 forward.

Interpretation:

- GICS History may be point-in-time and stock-level.
- It is not natively Ken French 49 compatible.
- A GICS-to-FF49 translation would be an additional construct/interface choice and would need separate validation.

## Current Metadata

Current Yahoo, current GICS, current SIC/NAICS or present-day vendor classifications cannot be used for confirmatory historical interaction research.

Interpretation:

- These sources create look-ahead risk because they can assign past observations using current classifications.

## Manual Assignment

Manual ticker-to-industry labels are rejected.

Interpretation:

- They are discretionary, hard to reproduce, and vulnerable to hindsight.
