# Reproducibility Report

## Determinism Check

Two independent validation runs were executed using the same configuration and input source:

```powershell
.venv\Scripts\python.exe research\implementations\liq_001\validate_liq_001.py --max-symbols 60 --output-dir output\liq_001_validation
.venv\Scripts\python.exe research\implementations\liq_001\validate_liq_001.py --max-symbols 60 --output-dir output\liq_001_validation_2
```

Both runs produced the same primary output hash:

```text
f479568e36974857dd75af42715a3ec3d80d86b587b4dbb67a8a9fc12c1c9d6f
```

## Reproducibility Interpretation

LIQ-001 uses deterministic formulas only.

With the same universe, same market data, same configuration, and same preprocessing, the implementation reproduces identical output.

## Boundary

Yahoo Finance can revise historical data. For permanent archival reproducibility, future stages should archive raw input snapshots.

