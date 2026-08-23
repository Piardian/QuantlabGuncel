# GOAL

Begin:

WOR-002

Workflow Out-of-Sample Reproducibility Audit

CSM-001 x TSM-001

Mission
-------

WOR-001 registered the protocol for testing whether the CSM-001 x TSM-001 nested composite workflow reproduces out of sample.

The purpose of WOR-002 is to execute that protocol.

This is NOT a performance study.

This is NOT an economic validation.

This is NOT production research.

--------------------------------------------------

Primary Research Question

Does the CSM-001 x TSM-001 nested workflow structure reproduce on data not used in CWS-001?

--------------------------------------------------

OOS Requirement

Use only dates after:

2025-12-30

No overlap with CWS-001 is permitted.

If insufficient OOS data exist, conclude:

Inconclusive

--------------------------------------------------

Required Analyses

1. OOS data availability check
2. Non-overlap verification
3. Frozen implementation verification
4. Common OOS sample reconstruction
5. OOS workflow state matrix
6. OOS nested-state analysis
7. OOS agreement metrics
8. OOS time stability analysis
9. OOS symbol coverage analysis
10. Reproducibility classification versus CWS-001

--------------------------------------------------

Forbidden

Do NOT:

- modify CSM-001
- modify TSM-001
- optimize parameters
- tune thresholds
- evaluate trading performance
- claim alpha
- evaluate economic utility
- recommend production deployment

--------------------------------------------------

Expected Outputs

Generate:

- wor002_oos_reproducibility_audit.md
- oos_data_availability.csv
- oos_workflow_state_matrix.csv
- oos_nested_state_analysis.csv
- oos_agreement_metrics.csv
- oos_time_stability_analysis.csv
- oos_symbol_coverage_analysis.csv
- reproducibility_comparison.csv
- limitations.md
- executive_summary.md
- wor002_manifest.json

--------------------------------------------------

Allowed Conclusions

Exactly one:

- Reproduced
- Partially Reproduced
- Not Reproduced
- Inconclusive
