# Analysis Plan

## Study Name

CWS-001: Composite Workflow Scientific Evaluation

## Required Analyses

1. Frozen input verification
2. Common sample reconstruction
3. State interaction matrix
4. Nested-state confirmation
5. Conditional information analysis
6. Incremental information analysis
7. Conflict-region analysis
8. Time stability analysis
9. Symbol coverage analysis
10. Scientific interpretation

## Registered State Definitions

CSM state:

- CSM_HIGH: `csm001_top_decile_flag == True`
- CSM_NOT_HIGH: `csm001_top_decile_flag == False`

TSM state:

- TSM_HIGH: `tsm001_positive_state == True`
- TSM_LOW: `tsm001_positive_state == False`

Interaction states:

- CSM_HIGH x TSM_HIGH
- CSM_HIGH x TSM_LOW
- CSM_NOT_HIGH x TSM_HIGH
- CSM_NOT_HIGH x TSM_LOW

## Registered Metrics

State structure:

- Observation count
- Coverage
- Jaccard similarity
- Precision
- Recall
- Phi association
- Nested-state coverage

Incremental information:

- Incremental R-squared
- Conditional mean differences
- Rank correlation
- Year-by-year stability
- Symbol coverage

Conflict analysis:

- Conflict-state count
- Conflict-state coverage
- Minimum sample adequacy
- Descriptive state profile

## Minimum Evidence Standard

Workflow support requires:

- Reproducible state reconstruction from frozen inputs
- Stable nested-state relationship across multiple years
- Non-negligible incremental information in at least one registered analysis dimension
- No conclusion driven by a single year or rare state

## Output Requirements

CWS-001 must generate:

- `cws001_composite_workflow_evaluation.md`
- `workflow_state_matrix.csv`
- `nested_state_analysis.csv`
- `conditional_information.csv`
- `incremental_information.csv`
- `conflict_region_analysis.csv`
- `time_stability_analysis.csv`
- `symbol_coverage_analysis.csv`
- `scientific_interpretation.md`
- `limitations.md`
- `executive_summary.md`
- `cws001_manifest.json`
