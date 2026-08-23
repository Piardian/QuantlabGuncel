# Execution Example

## Verification Execution

```powershell
.\.venv\Scripts\python.exe research\constructs\cor_001\verify_cor001.py
```

## Full Pipeline Execution

```powershell
.\.venv\Scripts\python.exe research\constructs\cor_001\cor001_correlation_pipeline.py --config research\constructs\cor_001\config.yaml
```

## Optional Close Panel Execution

```powershell
.\.venv\Scripts\python.exe research\constructs\cor_001\cor001_correlation_pipeline.py --config research\constructs\cor_001\config.yaml --close-panel path\to\close_panel.csv
```

## Expected Default Output

```text
output/cor001_correlation_state.csv
```

## Boundary

The full pipeline generates construct values only.

It does not run strategies, backtests, predictive validation, economic validation, or production evaluation.

