# Data Quality Report

## Source

Adjusted close data was downloaded from Yahoo Finance through `yfinance` and cached at `output/csm_001_cv001/adjusted_close_panel.csv`.

## Coverage

- Configured universe count: 503
- Downloaded columns: 503
- Failed or unavailable tickers: 2
- Failed ticker preview: FDXF, HONA
- Average valid coverage ratio: 0.8741
- Minimum coverage ratio, including required warmup: 0.0000
- Minimum coverage ratio after valid observations begin: 0.8370

## Important Limitation

The universe file is a current S&P 500-style ticker list. It is not a survivorship-free historical constituent database. CV-001 therefore validates implementation behavior under this available universe and does not claim historical constituent completeness.
