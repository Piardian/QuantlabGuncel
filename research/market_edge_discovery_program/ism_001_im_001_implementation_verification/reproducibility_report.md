# Reproducibility Report

## Procedure

The empirical Ken French 49 industry monthly return panel was transformed twice through the same deterministic ISM-001 implementation. The resulting construct frames were serialized in stable row order and hashed.

## Result

- In-memory deterministic hash: `4eaadd88981e704d290149293f7b8d41473d9ca3692e7351c7cf882dbbded9aa`
- Persisted artifact hash: `fb492d61a7aa6e279564b658a08cf764f642b8d43f482c0a33801584cfa645e7`
- Deterministic status: **Passed**

The implementation contains no random component and requires no random seed.

## Regeneration Commands

```powershell
.venv\Scripts\python.exe research\implementations\ism_001\prepare_ism_001_data.py
.venv\Scripts\python.exe research\implementations\ism_001\validate_ism_001.py
.venv\Scripts\python.exe research\implementations\ism_001\run_ism001_construct_generation.py
```
