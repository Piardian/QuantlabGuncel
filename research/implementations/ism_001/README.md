# ISM-001 Implementation

This directory implements the frozen ISM-001 construct:

**Ken French 49 Industry Portfolio 12-1 Cross-Sectional Momentum Rank**

The implementation is an engineering artifact only. It does not evaluate prediction, alpha, trading performance, portfolio construction or economic value.

## Run

```powershell
.venv\Scripts\python.exe research\implementations\ism_001\prepare_ism_001_data.py
.venv\Scripts\python.exe research\implementations\ism_001\validate_ism_001.py
.venv\Scripts\python.exe research\implementations\ism_001\run_ism001_construct_generation.py
```

## Frozen Definition

- Data source: Ken French 49 Industry Portfolios monthly value-weighted returns.
- Formation: compounded 12-1 return, months `t-12` through `t-2`.
- Cross-section: 49 industry portfolios.
- Rank: monthly percentile rank, average tie method.
- Labels: `TOP_DECILE`, `BOTTOM_DECILE`, `MIDDLE`, `INVALID`.
