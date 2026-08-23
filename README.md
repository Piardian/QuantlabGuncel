# QuantLab

**Quantitative Backtesting & Research Infrastructure**

QuantLab is a modular Python research platform for market-data ingestion, strategy execution, portfolio simulation, performance analysis, and reproducible backtesting experiments.

The project is designed around a separation between data, strategy logic, execution simulation, and research outputs rather than a single monolithic trading script.

## Architecture

```text
                 Configuration / CLI
                         │
                         ▼
                  Market Data Layer
                         │
                         ▼
                   Strategy Layer
                         │
                         ▼
                  Backtest Engine
                         │
                         ▼
             Portfolio / Execution Model
                         │
                         ▼
              Metrics & Performance Data
                         │
                  ┌──────┴──────┐
                  ▼             ▼
                Charts      Experiment Output
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

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run a standard backtest:

```powershell
py main.py --ticker AAPL --start 2020-01-01 --end 2024-01-01
```

Charts and generated artifacts are written to `output/` by default.

## Stock research path

The repository also contains a separate stock-research implementation of the existing v1.31 strategy under `strategies/stock_v131/`.

Example:

```powershell
py main.py --config config/backtest_stock_v131.json --ticker AAPL --start 2024-02-01 --end 2024-03-15 --no-plot
```

The stock v1.31 path currently expects 15-minute data. Yahoo Finance places retention limits on intraday history, so the available date range depends on the provider.

## Research methodology

QuantLab is intended to make research assumptions and outputs explicit. A backtest should be treated as an experiment with defined inputs, configuration, strategy logic, and evaluation metrics—not as proof of future market performance.

This distinction is important because historical performance can be affected by data quality, parameter selection, transaction assumptions, market regime, and overfitting.

## Engineering principles

- Reproducibility through configuration-driven experiments
- Separation of data, strategy, execution, and reporting concerns
- Explicit research artifacts
- Extensible strategy and data-provider boundaries
- Clear distinction between research infrastructure and live execution

## Validation & CI

The repository includes automated repository-level quality checks through GitHub Actions. Changes are checked in an isolated CI environment before being treated as validated repository state.

## Limitations

- Market-data availability depends on the upstream provider
- Historical backtests do not guarantee future results
- Provider-specific intraday retention can restrict experiment windows
- Research results depend on the assumptions and data supplied to the engine

## Roadmap

- Broader data-provider support
- More systematic experiment tracking
- Expanded research metrics
- Stronger automated validation
- Improved reproducibility and result comparison

## Technology

Python · Backtesting · Market Data · Quantitative Research · Portfolio Simulation · CLI · Data Analysis

## Status

**Active development / research infrastructure**

QuantLab is a research and engineering project. It is not a live-trading performance claim or financial advice.
