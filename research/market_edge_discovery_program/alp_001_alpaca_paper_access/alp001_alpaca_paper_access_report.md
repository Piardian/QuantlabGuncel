# ALP-001 — Alpaca Paper Access

## Program

Market Edge Discovery Program

## Purpose

ALP-001 prepares and verifies access to Alpaca Paper as a zero-cost development, exploratory and paper-execution environment.

This is not formal historical validation and not scientific T0.

## Current State

| Item | State |
|---|---|
| Paid data purchase | `DEFERRED` |
| FREE-001 | `FREE_DEVELOPMENT_ONLY` |
| Alpha logic | `FROZEN` |
| Formal performance | `FORBIDDEN` |
| Exploratory backtest | `AUTHORIZED_NON_FORMAL_AFTER_INTEGRATION` |
| Paper trading | `AUTHORIZED_AFTER_INTEGRATION` |
| Scientific T0 | `NOT_ESTABLISHED` |
| Production | `BLOCKED` |
| Real-money trading | `BLOCKED` |

## ALP-001 Goal

Verify that the owner has created an Alpaca Paper account and made credentials securely available to the local execution environment.

## Required PASS Condition

`GET /v2/account` against the Alpaca Paper endpoint must succeed using secure credentials.

## Current Evidence

No Alpaca credential environment variables were detected in the current environment.

No API key, secret, account status, or authenticated `/account` response is available.

## Decision

`ALPACA_ACCESS_NOT_READY`

## Interpretation

ALP-001 is staged but cannot pass until the owner creates Alpaca Paper credentials and stores them securely outside tracked research artifacts.

## Sources

- Alpaca Paper Trading documentation: https://docs.alpaca.markets/us/docs/paper-trading
- Alpaca Trading API Account endpoint: https://docs.alpaca.markets/reference/getaccount-1
- Alpaca Create Order endpoint: https://docs.alpaca.markets/us/reference/postorder

