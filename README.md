# QuantLab

**Quantitative Backtesting & Research Infrastructure**

![Status](https://img.shields.io/badge/status-active%20development-blue)
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Backtesting](https://img.shields.io/badge/Backtesting-Research-orange)
![Data](https://img.shields.io/badge/Data-Market%20Data-green)

QuantLab is a modular Python research platform for market-data ingestion, strategy execution, portfolio simulation, performance analysis, and reproducible backtesting experiments.

## Architecture

```text
Configuration / CLI
        ↓
Market Data Layer
        ↓
Strategy Layer
        ↓
Backtest Engine
        ↓
Portfolio / Execution Model
        ↓
Metrics & Performance Data
        ↓
Charts + Experiment Output
```

## Core capabilities

- Configuration-driven backtests
- Market-data acquisition and normalization
- Modular strategy interfaces
- Portfolio and execution simulation
- Performance metrics and reporting
- Chart generation
- CLI-based experiment execution
- Separate research and operational concerns
- Stock research path for the v1.31 strategy port

## Evidence & research artifacts

The repository contains concrete research outputs and operational components including performance dashboards, signal reports, structured logging, portfolio state handling, and generated experiment artifacts.

Performance metrics are treated as research outputs. They are not presented as evidence of future trading profitability.

## Repository structure

```text
config/       Configuration and experiment settings
data/         Market-data providers and normalization
engine/       Backtest orchestration, metrics, plotting
strategies/   Strategy implementations and abstractions
main.py       CLI entry point
output/       Generated research artifacts
```

## Quick start

```powershell
py -m pip install -r requirements.txt
py main.py --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

Charts and generated artifacts are written to `output/` by default.

## Stock research path

A separate stock-research implementation of the existing v1.31 strategy is available under `strategies/stock_v131/`.

```powershell
py main.py --config config/backtest_stock_v131.json --ticker AAPL --start 2024-02-01 --end 2024-03-15 --no-plot
```

## Research methodology

A backtest is treated as an experiment with defined inputs, configuration, strategy logic, and evaluation metrics—not as proof of future market performance.

Historical results can be affected by data quality, parameter selection, transaction assumptions, market regime, and overfitting.

## Validation & CI

The repository includes automated repository-level quality checks through GitHub Actions. Changes are checked in an isolated CI environment before being treated as validated repository state.

## Limitations

- Market-data availability depends on the upstream provider
- Historical backtests do not guarantee future results
- Intraday retention can restrict experiment windows
- Research results depend on the assumptions and data supplied to the engine

## Technology

Python · Backtesting · Market Data · Quantitative Research · Portfolio Simulation · CLI · Data Analysis

## Status

**Active development / research infrastructure**

QuantLab is a research and engineering project, not a live-trading performance claim or financial advice.
