# FUND-001 / IM-001

# Execution Example

Run verification with live FRED download:

```powershell
.venv\Scripts\python.exe research\implementations\fund_001\validate_fund_001.py --config research\implementations\fund_001\config.yaml
```

Run verification with explicit frozen input CSVs:

```powershell
.venv\Scripts\python.exe research\implementations\fund_001\validate_fund_001.py --cp-csv path\to\DCPF3M.csv --tbill-csv path\to\DTB3.csv
```

The official output is:

```text
output/fund_001_validation/fund001_funding_stress_output.csv
```

