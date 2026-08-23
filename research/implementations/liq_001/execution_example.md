# Execution Example

Run the default validation:

```powershell
.venv\Scripts\python.exe research\implementations\liq_001\validate_liq_001.py --config research\implementations\liq_001\config.yaml
```

Run the capped validation used in IM-001:

```powershell
.venv\Scripts\python.exe research\implementations\liq_001\validate_liq_001.py --max-symbols 60 --output-dir output\liq_001_validation
```

Primary output:

```text
output/liq_001_validation/liq001_liquidity_output.csv
```

Verification summary:

```text
output/liq_001_validation/verification_summary.json
```

