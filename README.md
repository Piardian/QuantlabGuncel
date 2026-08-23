# QuantLab — Backtesting & Research Infrastructure

A modular Python backtesting system for reproducible strategy research, market-data ingestion, portfolio simulation, metrics, and experiment output.

## Architecture

```text
CLI / Configuration
        ↓
Market Data Provider
        ↓
Strategy Layer
        ↓
Backtest Engine
        ↓
Portfolio / Execution Simulation
        ↓
Metrics + Charts + Experiment Output
```

## Core components

- `config/` — centralized configuration and defaults
- `data/` — market-data providers and normalization
- `engine/` — backtest orchestration, metrics, and plotting
- `strategies/` — strategy implementations and base abstractions
- `main.py` — command-line entry point
- `output/` — generated research artifacts

## Run a backtest

```powershell
py -m pip install -r requirements.txt
py main.py --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

Charts are written to `output/` by default.

## Stock research path

The repository also contains a separate stock-research port of the existing v1.31 strategy logic under `strategies/stock_v131/`. The original MT5/forex files remain isolated from this path.

```powershell
py main.py --config config/backtest_stock_v131.json --ticker AAPL --start 2024-02-01 --end 2024-03-15 --no-plot
```

The stock v1.31 path currently expects 15-minute data. Yahoo Finance intraday history is subject to provider retention limits, so recent date ranges may be required.

## Engineering principles

- Reproducible configuration-driven experiments
- Separation of data, strategy, execution, and reporting concerns
- Explicit research outputs rather than opaque results
- Extensible strategy and data-provider boundaries
- Clear separation between research code and operational automation

## Status

**Active development / research infrastructure.**

This repository is intended for engineering and research validation. Historical backtest results should not be interpreted as evidence of future trading performance.
