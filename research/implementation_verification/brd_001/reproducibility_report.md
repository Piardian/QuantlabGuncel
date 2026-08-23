# BRD-001 / IM-001: Reproducibility Report

## Purpose

Document reproducibility controls for the BRD-001 implementation.

## Deterministic Controls

The implementation uses:

- sorted ticker universe
- sorted date index
- sorted close-panel columns
- fixed SMA window
- fixed normalization window
- fixed minimum eligible count
- deterministic percentile tie handling
- deterministic CSV serialization
- SHA-256 output hashing

## Repeated Execution Check

The verification script computes BRD-001 twice on the same synthetic input panel.

The two output hashes matched.

Result:

```text
PASS
```

Hash:

```text
0bd625913388108f0dc5e48d705b1d54f2189de41ef873c08f173d78dc42b5ea
```

## Reproduction Command

```powershell
.\.venv\Scripts\python.exe research\constructs\brd_001\verify_brd001.py
```

## Notes

Full-market Yahoo downloads may vary if the upstream data vendor revises historical data.

The implementation itself is deterministic for a fixed input panel.

