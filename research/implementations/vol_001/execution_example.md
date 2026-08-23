# Execution Example

## Live Data Validation

```powershell
.venv\Scripts\python.exe research\implementations\vol_001\validate_vol_001.py --config research\implementations\vol_001\config.yaml --output-dir output\vol_001_validation
```

## Frozen Input Reproducibility Check

```powershell
.venv\Scripts\python.exe research\implementations\vol_001\validate_vol_001.py --config research\implementations\vol_001\config.yaml --input-csv output\vol_001_validation_fidelity_a\vol001_input_ohlc.csv --output-dir output\vol_001_validation_snapshot
```

## Expected Output Files

- `vol001_input_ohlc.csv`
- `vol001_volatility_output.csv`
- `verification_summary.json`
- `verification_report.md`
- `reproducibility_report.md`
- `unit_test_report.md`
- `execution_example.md`
- `limitations.md`
- `executive_summary.md`

