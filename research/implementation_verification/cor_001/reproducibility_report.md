# Reproducibility Report

## Reproducibility Status

PASS

## Deterministic Execution

The verification script executed the construct twice on the same deterministic synthetic close panel.

Both runs produced identical frame hashes.

## Verification Hash

```text
beb1e376a03388b9aa148886fe84fca81e2a09c92836fd48c3b5a2318ee74733
```

## Reproduction Command

```powershell
.\.venv\Scripts\python.exe research\constructs\cor_001\verify_cor001.py
```

## Configuration

Default implementation configuration is stored at:

```text
research/constructs/cor_001/config.yaml
```

## Notes

Full-market data generation is intentionally deferred to CV-001.

IM-001 validates implementation fidelity, not empirical construct validity.

