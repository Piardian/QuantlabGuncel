# OPT-001 / IM-001

# Execution Example

Run verification with live FRED download:

```powershell
.venv\Scripts\python.exe research\implementations\opt_001\validate_opt_001.py --config research\implementations\opt_001\config.yaml
```

Run verification with explicit frozen input CSV:

```powershell
.venv\Scripts\python.exe research\implementations\opt_001\validate_opt_001.py --input-csv path\to\VIXCLS.csv
```

The official output is:

```text
output/opt_001_validation/opt001_options_implied_output.csv
```

