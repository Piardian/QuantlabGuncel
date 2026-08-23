# RRV-002 Selected Candidate Specification

Selected candidate universe: RRV002_FREE_US_EQUITY_250

Size: 250

Selection rule:

1. Active tradable US equity assets from Alpaca.
2. Exchange in NYSE, NASDAQ, or AMEX.
3. Simple symbol pattern 1-5 uppercase letters.
4. Exclude securities whose names reliably indicate ETF, ETN, fund, warrant, right, unit, preferred, ADR/ADS, note, trust, or SPAC.
5. Require at least one CSM-capable observation under frozen 252/21 history semantics.
6. Sort by usable_bar_count descending, coverage_percentage descending, symbol ascending.
7. Select the smallest predefined candidate satisfying >=50 eligible securities on at least 90% of rebalance dates and median eligible count >=100.

Universe hash: BB0886CDDABB93D1B429378732EFCA5D6EB67BA5F29D0B75E46040337ADE918B

Performance-based selection used: NO
