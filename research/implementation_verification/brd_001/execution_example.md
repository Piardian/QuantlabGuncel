# BRD-001 / IM-001: Execution Example

## Verification Execution

To run deterministic implementation verification:

```powershell
.\.venv\Scripts\python.exe research\constructs\brd_001\verify_brd001.py
```

Expected result:

```text
status: PASS
```

## Full Pipeline Execution

To run the BRD-001 pipeline with the frozen config:

```powershell
.\.venv\Scripts\python.exe research\constructs\brd_001\brd001_breadth_pipeline.py --config research\constructs\brd_001\config.yaml
```

## CSV Close-Panel Execution

To run from a prebuilt close-panel CSV:

```powershell
.\.venv\Scripts\python.exe research\constructs\brd_001\brd001_breadth_pipeline.py --config research\constructs\brd_001\config.yaml --close-panel path\to\close_panel.csv
```

The close-panel CSV must contain:

- `date`
- one ticker column per security

## Output

Default output:

```text
output/brd001_breadth_state.csv
```

The command prints a JSON summary including output path, row count, valid observation count, universe count and output hash.

