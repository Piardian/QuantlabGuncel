# RSM-001 Implementation

RSM-001 implements the frozen CD-001 construct:

**Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank**

The implementation is deterministic and reproduces the CD-001 specification:

- Monthly security returns.
- Monthly Fama-French 3-factor returns and risk-free rate.
- Rolling 36-month OLS residualization.
- Minimum 24 valid observations.
- 12-1 residual aggregation using residuals from `t-12` through `t-2`.
- 36-month residual volatility standardization.
- Cross-sectional percentile ranking.
- `TOP_DECILE`, `BOTTOM_DECILE`, `MIDDLE`, `INVALID` state labels.

No backtest, alpha claim, parameter optimization, or economic validation is included.

## Verification

Run:

```powershell
.venv\Scripts\python.exe research\implementations\rsm_001\validate_rsm_001.py
```

The validator uses deterministic synthetic data to verify schema, reproducibility, frozen-parameter guards, factor-input guards, and output bounds.

Generate the empirical construct state after data preparation:

```powershell
.venv\Scripts\python.exe research\implementations\rsm_001\prepare_rsm_001_data.py
.venv\Scripts\python.exe research\implementations\rsm_001\run_rsm001_construct_generation.py
```

## Data Status

Repository-local RSM-001 empirical input files now exist:

- `data/rsm_001/monthly_returns.csv`
- `data/rsm_001/fama_french_3_factor_monthly.csv`

Empirical state output:

- `output/rsm_001/rsm001_residual_momentum_state.csv`
