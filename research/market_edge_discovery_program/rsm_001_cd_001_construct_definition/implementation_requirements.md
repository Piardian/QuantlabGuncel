# Implementation Requirements

IM-001 must implement:

- Monthly security return builder.
- Fama-French factor loader or downloader.
- Factor alignment validation.
- Rolling 36-month OLS residualization.
- Minimum observation enforcement.
- 12-1 residual aggregation.
- Residual volatility calculation.
- Cross-sectional percentile ranking.
- State assignment.
- Exclusion report.
- Reproducibility report.

IM-001 must abort if factor data cannot be obtained or aligned.
