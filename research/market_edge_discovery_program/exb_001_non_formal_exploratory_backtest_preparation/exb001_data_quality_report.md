# EXB-001 Data Quality Report

## Dataset Summary

| Metric | Value |
| --- | --- |
| Dataset ID | EXB001_ALPACA_IEX_DAILY_REDUCED |
| Requested symbols | 100 |
| Symbols with rows | 100 |
| Row count | 91,986 |
| Feed | iex |
| Adjustment | raw |
| Timeframe | 1Day |

## Quality Counts

| Check | Count |
| --- | ---: |
| Duplicate symbol-date rows | 0 |
| Invalid OHLC relationships | 0 |
| Negative or zero prices | 0 |
| Zero or negative volume rows | 17,393 |
| Missing symbol-trading-date observations | 48,714 |

## Assessment

The dataset is usable for non-formal exploratory preparation, but it contains major completeness and volume limitations.

The dataset is not suitable for formal production-grade alpha validation.
