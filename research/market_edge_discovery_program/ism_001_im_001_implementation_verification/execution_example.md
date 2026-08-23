# Execution Example

Run from repository root:

```powershell
.venv\Scripts\python.exe research\implementations\ism_001\prepare_ism_001_data.py
.venv\Scripts\python.exe research\implementations\ism_001\validate_ism_001.py
.venv\Scripts\python.exe research\implementations\ism_001\run_ism001_construct_generation.py
```

Expected primary outputs:

- `data/ism_001/ken_french_49_industry_value_weighted_monthly.csv`
- `data/ism_001/data_preparation_report.json`
- `output/ism_001/ism001_industry_momentum_state.csv`
- `output/ism_001/ism001_generation_report.json`
