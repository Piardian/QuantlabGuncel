# VOL-001 / IM-001

Implementation Development & Verification for VOL-001.

Frozen construct:

**US Equity Market Daily Yang-Zhang Volatility State**

Run:

```powershell
.venv\Scripts\python.exe research\implementations\vol_001\validate_vol_001.py --config research\implementations\vol_001\config.yaml
```

Reproducibility check with a frozen input snapshot:

```powershell
.venv\Scripts\python.exe research\implementations\vol_001\validate_vol_001.py --input-csv output\vol_001_validation\vol001_input_ohlc.csv --output-dir output\vol_001_validation_snapshot
```
