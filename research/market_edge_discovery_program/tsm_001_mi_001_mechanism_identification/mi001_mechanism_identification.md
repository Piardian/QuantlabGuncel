# TSM-001 / MI-001 Mechanism Identification

## Purpose

Identify what observable market behavior is represented by the frozen TSM-001 Raw 12-1 Time-Series Momentum State.

No future returns, alpha, trading performance, backtests, volatility scaling or economic value were evaluated.

## Evidence Base

- Source state file: `output/tsm_001_cv001/tsm001_construct_state.csv`
- Valid observations: 1,768,840
- Unique tickers: 499
- Date range: 2011-01-03 to 2025-12-30

## State Profile

- POSITIVE state observation share: 0.7228
- NEGATIVE state observation share: 0.2772
- POSITIVE median raw 12-1 return: 0.2205
- NEGATIVE median raw 12-1 return: -0.1190
- POSITIVE mean absolute raw 12-1 magnitude: 0.2935
- NEGATIVE mean absolute raw 12-1 magnitude: 0.1523

## Persistence Profile

- POSITIVE median duration: 4.0 trading days
- NEGATIVE median duration: 3.0 trading days
- POSITIVE p90 duration: 169.0 trading days
- NEGATIVE p90 duration: 51.0 trading days

## Mechanism Interpretation

Supported by evidence:

TSM-001 represents a signed intermediate-horizon own-trend state. The POSITIVE state corresponds to securities whose adjusted close 21 trading days ago exceeded their adjusted close 252 trading days ago. The NEGATIVE state corresponds to securities whose adjusted close 21 trading days ago was below their adjusted close 252 trading days ago.

Supported by evidence:

The construct behaves as a persistent direction-state construct rather than a high-frequency timing signal. State runs frequently persist for multiple trading weeks, consistent with the 12-1 measurement window.

Supported by evidence:

At the market-panel level, TSM-001 also produces a descriptive time-varying breadth measure: the fraction of securities in POSITIVE or NEGATIVE own-trend states.

Not evaluated:

Whether these states predict future returns, future volatility, drawdowns, alpha, portfolio outcomes or economic utility.

## Final MI-001 Conclusion

**Supported by evidence**

The evidence supports interpreting TSM-001 as a raw intermediate-horizon own-trend direction construct with persistent state behavior. This conclusion is explanatory and descriptive only.
