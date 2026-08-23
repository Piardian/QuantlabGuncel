# Python Backtesting System

Clean, modular, and extensible stock market backtesting infrastructure built with Backtrader and Yahoo Finance data.

## Structure

- `config/`: central configuration and defaults
- `data/`: market data providers
- `engine/`: backtest orchestration, plotting, and metrics
- `strategies/`: base strategy class and strategy implementations
- `main.py`: CLI entry point

## Install

```powershell
py -m pip install -r requirements.txt
```

## Run

```powershell
py main.py --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

Charts are saved under `output/` by default.

## Stock Research Port Of v1.31

This repo now also contains a separate stock-research port of the existing `v1.31` forex bot logic. The MT5 forex files remain untouched; the stock test path lives in new Python files under `strategies/stock_v131/`.

Example:

```powershell
py main.py --config config/backtest_stock_v131.json --ticker AAPL --start 2024-02-01 --end 2024-03-15 --no-plot
```

Notes:

- `trendflowing_stock_v131` currently expects `15m` data.
- Yahoo Finance intraday history is limited, so use relatively recent date ranges.
