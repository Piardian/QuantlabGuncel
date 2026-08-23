# EXB-001 Preparation Report

Program: Market Edge Discovery Program  
Stage: EXB-001 - Non-Formal Exploratory Backtest Preparation  
Evidence label: NON_FORMAL_EXPLORATORY_EVIDENCE  
Date: 2026-08-12

## Purpose

EXB-001 prepares a restricted, non-formal exploratory backtest environment using accessible Alpaca historical data.

This stage does not evaluate profitability, alpha, Sharpe, CAGR, drawdown, hit rate, benchmark outperformance, equity curves, strategy PnL, or portfolio performance.

## Current Inputs

- Alpaca Paper account access: verified in ALP-001.
- Alpaca read-only integration: verified in ALP-002.
- Alpaca broker adapter and local order-safety layer: verified in ALP-003.
- Order mutation calls during EXB-001: 0.
- Alpha/model logic changes during EXB-001: none.

## Prepared Components

- Historical daily bar access was verified.
- Deterministic reduced universe selection was specified.
- Dataset request parameters were frozen for exploratory use.
- Data schema was documented.
- Warm-up, rebalance, execution timing, missing data, price adjustment, benchmark, and cost policies were frozen for EXB-002.
- Bias and limitation registers were created.

## Evidence Boundary

All EXB-001 outputs are preparation artifacts only. They may support a non-formal exploratory backtest in EXB-002, but they do not support production claims or formal alpha validation.

## Decision

EXB-001 preparation is verified for non-formal exploratory use only.

Authorized next stage: EXB-002 - Non-Formal Exploratory Backtest Execution.

Not authorized: PAPER-001, real-money execution, production deployment, formal robustness validation.
