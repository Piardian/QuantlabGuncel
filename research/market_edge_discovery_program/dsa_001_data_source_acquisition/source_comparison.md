# Source Comparison

## Institutional Stack

The CRSP + Compustat PIT + CCM + I/B/E/S + GICS History stack is the best scientific candidate.

Strengths:

- CRSP supports US active/inactive securities, permanent identifiers, market data, and corporate actions.
- Compustat PIT supports point-in-time financial statements.
- CCM provides historical CRSP/Compustat linking.
- I/B/E/S provides analyst forecast timelines required for expectation-based PEAD research.
- GICS History supports historical industry classification for CSM x ISM work.

Limitations:

- Requires institutional/commercial licensing.
- Not locally available now.
- Local schema inspection is still mandatory.
- PEAD may still require precise announcement timestamps beyond date-only fields, depending on study design.

## Commercial Accessible Stack

Sharadar/Nasdaq Data Link/QuantRocket is a serious partial candidate.

Strengths:

- Active and delisted coverage is claimed.
- PIT-ready US fundamentals are claimed.
- S&P 500 constituent history and SEC 8-K events are documented through QuantRocket.
- More accessible than WRDS/CRSP/Compustat for an individual project.

Limitations:

- Must audit PIT semantics directly.
- Identifier lineage is likely less academically standard than PERMNO/GVKEY/CCM.
- Does not fully solve analyst expectation timing for PEAD.
- May not solve point-in-time GICS history.

## Rejected For DSA Purposes

Current Yahoo metadata, current ticker lists, manual sector labels, and current GICS/SIC snapshots are rejected for PIT/survivorship research.
