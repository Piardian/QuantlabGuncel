# Implementation Requirements

IM-001 must:

- Download or load Ken French 49 Industry Portfolios monthly value-weighted returns from a documented source.
- Parse monthly returns deterministically.
- Convert percentage returns to decimals if required.
- Compute 12-1 compounded industry returns.
- Rank valid industries cross-sectionally by month.
- Apply frozen decile labels.
- Serialize deterministic outputs.
- Provide validation and reproducibility reports.

IM-001 must not:

- Change taxonomy.
- Change weighting.
- Change formation window.
- Add stock-level membership.
- Run backtests.
- Claim alpha.
- Optimize parameters.

