# GOAL

Begin:

DBA-001

Data & Bias Audit

## Mission

Audit whether the current research dataset and workflow evidence are sufficiently clean to support net-of-cost and production-readiness evaluation.

This is not a strategy optimization task.

This is not an alpha research task.

## Primary Research Question

What data, bias, timing and research-design limitations could invalidate or weaken the current CSM x TSM workflow evidence?

## Scope

Evaluate:

- CSM-001
- TSM-001
- CSM x TSM workflow
- WPC-002 gross portfolio construction
- existing data sources and output artifacts

## Required Audit Areas

1. Survivorship bias
2. Current-constituent universe limitation
3. Delisted security absence
4. Point-in-time membership limitation
5. Signal timestamp vs execution timestamp
6. Same-close execution risk
7. Adjusted close handling
8. Missing data
9. Liquidity coverage
10. Repeated testing / research degrees of freedom
11. Benchmark comparability
12. Cost-model readiness

## Forbidden

Do not:

- modify constructs
- modify workflow rules
- optimize parameters
- run new alpha tests
- recommend production deployment
- claim profitability

## Expected Outputs

Generate:

- dba001_data_bias_audit.md
- bias_risk_matrix.csv
- data_source_inventory.csv
- timing_assumption_audit.md
- survivorship_bias_assessment.md
- point_in_time_assessment.md
- cost_model_readiness.md
- benchmark_readiness.md
- limitations.md
- executive_summary.md

## Allowed Conclusions

Exactly one:

- Audit Passed
- Audit Passed With Limitations
- Audit Failed
- Inconclusive

## Success Criteria

DBA-001 is complete only if it clearly identifies whether the current research evidence is suitable for net-of-cost validation, and which limitations must be carried forward.
