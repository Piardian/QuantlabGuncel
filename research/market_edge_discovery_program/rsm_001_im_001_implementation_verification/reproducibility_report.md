# Reproducibility Report

## Deterministic Execution

The synthetic validation was executed twice within the validator and produced identical output hashes.

Deterministic hash:

```text
e2a6c762ab0ba7e910866ffd62b4e38d48023cde0d23b161fb3fbadc333d451d
```

## Reproducibility Requirements

Complete empirical reproducibility requires:

- Monthly security return panel.
- Monthly Fama-French 3-factor return panel.
- Monthly risk-free rate.
- Frozen CD-001 configuration.
- Source code in `research/implementations/rsm_001`.

## Empirical Reproducibility

Empirical state generation was executed with deterministic repeat hashing inside `run_rsm001_construct_generation.py`.

Empirical persisted-artifact hash:

```text
217cc97a31084547845e2d970467e059ff8df0a161e7db6708950f89537e5bba
```

Full regeneration is now possible from:

- `data/rsm_001/monthly_returns.csv`
- `data/rsm_001/fama_french_3_factor_monthly.csv`
- `research/implementations/rsm_001/config.yaml`
- `research/implementations/rsm_001/run_rsm001_construct_generation.py`
