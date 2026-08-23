# EXB-001 Universe Specification

## Universe Purpose

The EXB-001 universe exists only to support non-formal exploratory execution in EXB-002.

It is not a formal point-in-time research universe and must not be used for production claims.

## Deterministic Selection Rule

Universe candidates are selected from Alpaca assets using the following non-performance-based rule:

1. Asset status is active.
2. Asset is tradable.
3. Asset class is us_equity.
4. Exchange is NYSE, NASDAQ, or NYSE American after normalization.
5. Obvious non-common-stock symbols are excluded when identifiable from the symbol or asset attributes.
6. Remaining symbols are sorted alphabetically.
7. The first 100 symbols are selected.

## Frozen Universe Size

Selected count: 100 symbols.

## Explicitly Not Used

Existing project files containing performance ranks, volatility ranks, or prior research-selected universes are not used for EXB-001 universe selection.

## Limitations

- The universe is current-active and not survivorship-free.
- Delisted securities are not reconstructed.
- Historical investability is not point-in-time complete.
- Sector and industry history are not frozen.
- The universe is reduced for exploratory feasibility.

## Evidence Classification

NON_FORMAL_EXPLORATORY_EVIDENCE.
