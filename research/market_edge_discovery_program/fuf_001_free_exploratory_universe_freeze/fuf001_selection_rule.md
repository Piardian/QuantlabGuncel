# FUF-001 Selection Rule

Selection rule: FROZEN

1. Start from RRV-002 Alpaca active tradable US equity assets.
2. Exchange must be NYSE, NASDAQ, or AMEX.
3. Symbol must match simple 1-5 uppercase letter pattern.
4. Exclude securities whose names reliably indicate ETF, ETN, fund, warrant, right, unit, preferred, ADR/ADS, note, trust, or SPAC.
5. Require CSM history capability under frozen 252/21 semantics.
6. Sort by usable_bar_count descending, coverage_percentage descending, symbol ascending.
7. Select the smallest predefined candidate satisfying >=50 eligible securities on at least 90% of rebalance dates and median eligible count >=100.

PERFORMANCE_BASED_SELECTION = NO
