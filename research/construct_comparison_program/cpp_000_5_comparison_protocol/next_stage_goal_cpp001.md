# /goal

# RESEARCH PROGRAM

Construct Comparison Program (CPP)

CPP-001

Data Inventory & Alignment Audit

--------------------------------------------------

## BACKGROUND

CPP-000 established the Program Charter and Frozen Evidence Registry.

CPP-000.5 froze the Comparison Protocol Registration.

No statistical construct comparison has been performed yet.

--------------------------------------------------

## PURPOSE

Audit the available frozen construct output datasets and determine whether they can be aligned for valid CPP comparison.

CPP-001 is a data-readiness and alignment stage only.

It must not draw dependence, redundancy, incremental information, or hierarchy conclusions.

--------------------------------------------------

## REQUIRED TASKS

- Locate frozen output series for each construct.
- Identify primary construct value columns.
- Report date range and observation count for each construct.
- Report missingness and data-quality flags where available.
- Build common-sample eligibility table.
- Build pairwise-overlap matrix.
- Determine which analyses from CPP-000.5 are eligible based on sample-size rules.
- Document all unresolved data-quality limitations.

--------------------------------------------------

## FORBIDDEN

Do NOT:

- compute correlations,
- compute mutual information,
- run regression,
- classify redundancy,
- infer complementarity,
- infer hierarchy,
- change constructs,
- optimize sample selection.

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- `cpp001_data_inventory.md`
- `construct_output_registry.csv`
- `date_coverage_summary.csv`
- `missingness_report.csv`
- `pairwise_overlap_matrix.csv`
- `common_sample_report.md`
- `analysis_eligibility_matrix.csv`
- `data_quality_limitations.md`
- `executive_summary.md`

--------------------------------------------------

## SUCCESS CRITERIA

CPP-001 succeeds if it determines which frozen construct outputs are available, alignable, and eligible for later preregistered comparison analyses.

No statistical comparison conclusions are permitted.
