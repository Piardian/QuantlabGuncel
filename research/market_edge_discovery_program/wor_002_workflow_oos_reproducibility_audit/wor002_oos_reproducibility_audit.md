# WOR-002: Workflow Out-of-Sample Reproducibility Audit

## Purpose

Test whether the CSM-001 x TSM-001 nested workflow structure reproduces on non-overlapping OOS data after 2025-12-30.

## Final Conclusion

**Reproduced**

## Data Availability

- Configured universe count: 503
- Downloaded columns: 503
- Failed symbols: 0
- OOS observations: 72,969
- OOS dates: 146
- OOS tickers: 500

## Evidence Classification

Supported by evidence:

- OOS observations are non-overlapping with CWS-001.
- Frozen CSM-001 and TSM-001 pipelines were used without parameter changes.
- OOS workflow state matrix and agreement metrics were generated.

Conclusion-specific evidence:

- P(TSM_HIGH | CSM_HIGH): 1.000000
- P(CSM_HIGH | TSM_HIGH): 0.152512
- CSM_HIGH x TSM_LOW count: 0

Not supported:

- Any production deployment claim.
- Any alpha claim.
- Any economic utility claim.

## Outputs

- `oos_data_availability.csv`
- `oos_workflow_state_matrix.csv`
- `oos_nested_state_analysis.csv`
- `oos_agreement_metrics.csv`
- `oos_time_stability_analysis.csv`
- `oos_symbol_coverage_analysis.csv`
- `reproducibility_comparison.csv`
