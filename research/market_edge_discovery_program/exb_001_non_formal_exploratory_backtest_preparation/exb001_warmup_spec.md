# EXB-001 Warm-Up Specification

## Frozen Warm-Up

Minimum warm-up: 252 trading days.

## Calendar Verification

Using the Alpaca trading calendar:

- First dataset trading day: 2021-01-04
- 252nd trading day completes on: 2021-12-31
- First eligible decision day after warm-up: 2022-01-03

## Rule

No symbol may be considered eligible for any exploratory signal calculation until it has sufficient available history for the frozen warm-up requirement.

## Missing Data Interaction

If a symbol has missing bars inside the warm-up window, the symbol remains ineligible until the required usable history is available.
