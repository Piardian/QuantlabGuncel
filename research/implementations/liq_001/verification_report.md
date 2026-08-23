# LIQ-001 Verification Report

## Scope

This report verifies implementation fidelity for the frozen LIQ-001 construct.

It does not evaluate prediction, alpha, profitability, or economic utility.

## Verification Run

Command:

```powershell
.venv\Scripts\python.exe research\implementations\liq_001\validate_liq_001.py --max-symbols 60 --output-dir output\liq_001_validation
```

## Verification Summary

- Requested symbols: 60
- Loaded symbols: 59
- Failed symbols: 1
- Rows produced: 4,023
- Date range: 2010-01-05 to 2025-12-31
- Mean eligible count: 55.95
- Mean coverage ratio: 0.9483
- Output SHA256: `f479568e36974857dd75af42715a3ec3d80d86b587b4dbb67a8a9fc12c1c9d6f`

## Column Verification

The primary output includes all required CD-001 columns:

- `date`
- `aggregate_illiquidity`
- `liq001_illiquidity_20d`
- `liq001_zscore`
- `eligible_count`
- `coverage_ratio`

## Data Issue

Ticker `BF.B` failed through Yahoo Finance for the validation run.

This did not invalidate the implementation test because 59 symbols loaded successfully and the minimum eligible-security rule remained satisfied.

## Final Implementation Classification

**Successfully implemented**

