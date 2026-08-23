# Limitations

- PV-001 uses SPY as the sole market proxy, as frozen in CD-001.
- Forecast horizons are fixed at 5, 20, and 60 trading days.
- Future high-volatility occurrence uses VOL-001's own historical top-20% state definition as a binary risk-state target.
- The Brier diagnostic uses percentile rank as a simple score, not a trained probability model.
- Predictive validation does not imply alpha, trading performance, economic utility, or production suitability.
- No Sharpe, CAGR, portfolio simulation, or profitability analysis is performed.
