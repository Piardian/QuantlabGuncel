# BRD-001 / IM-001: Limitations

## Vendor Data Limitation

The implementation is deterministic for fixed input data.

Yahoo Finance data may be revised by the vendor.

## Universe Limitation

The implementation uses `sp500_current_universe.csv`, consistent with CD-001.

This is not a survivorship-free historical constituent universe.

## Scope Limitation

IM-001 does not test construct validity.

IM-001 does not evaluate predictive validity, economic value, trading performance, profitability, or alpha.

## Full-Scale Execution Limitation

The verification run used a deterministic synthetic dataset.

Full-universe empirical validation belongs to CV-001.

## Dependency Limitation

Full Yahoo execution requires `yfinance`.

The synthetic verification path requires only pandas and numpy.

