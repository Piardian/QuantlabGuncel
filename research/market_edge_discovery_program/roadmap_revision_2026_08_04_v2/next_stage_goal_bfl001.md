# GOAL

Begin:

BFL-001

Baseline Freeze & Research Ledger

## Mission

Freeze the current CSM-001 x TSM-001 workflow and research assumptions before starting DBA-001, RVP-001, NOC, benchmark, capacity or production-readiness work.

This is a governance and reproducibility stage.

It is not an experiment.

## Primary Research Question

What exact model, data, universe, assumptions and historical research ledger are being carried forward into validation?

## Required Freeze Items

Freeze and document:

- data files and versions
- universe construction rule
- CSM-001 formula and source artifact
- TSM-001 formula and source artifact
- CSM x TSM workflow definition
- lookback windows
- ranking methods
- state definitions
- selected stock fraction
- rebalance frequency
- signal timestamp
- execution timestamp assumption
- weighting policy currently used
- WPC-002 gross portfolio accounting policy
- current headline metrics
- prior major research stages
- prior failed or blocked studies
- code version or file hashes if git commit is unavailable

## Required Outputs

Generate:

- bfl001_baseline_freeze.md
- frozen_model_specification.md
- frozen_data_inventory.csv
- frozen_artifact_hashes.csv
- research_ledger.md
- validation_carry_forward_assumptions.md
- modification_policy.md
- limitations.md
- executive_summary.md
- bfl001_manifest.json

## Forbidden

Do not:

- modify constructs
- modify workflow rules
- tune parameters
- run new performance tests
- optimize anything
- recommend production deployment

## Allowed Conclusion

Exactly one:

- Baseline Frozen
- Baseline Frozen With Limitations
- Baseline Freeze Blocked

## Success Criteria

BFL-001 is complete only if the validation baseline is reproducibly documented and future stages can verify whether anything changed.
