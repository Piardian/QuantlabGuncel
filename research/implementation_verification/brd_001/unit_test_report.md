# BRD-001 / IM-001: Unit Test Report

## Test Scope

Unit-style verification was performed through:

```text
research/constructs/brd_001/verify_brd001.py
```

## Tests Performed

- Output schema validation
- Deterministic repeated execution
- Eligible security count validation
- Above-SMA200 count validation
- Percent-above-SMA200 validation
- Normalization warmup validation
- Python compile validation

## Commands Executed

```powershell
.\.venv\Scripts\python.exe research\constructs\brd_001\verify_brd001.py
```

```powershell
.\.venv\Scripts\python.exe -m py_compile research\constructs\brd_001\brd001_breadth_pipeline.py research\constructs\brd_001\verify_brd001.py
```

## Result

All verification checks passed.

## Limitation

No full-universe empirical run was performed in IM-001.

That belongs to CV-001 and later stages.

