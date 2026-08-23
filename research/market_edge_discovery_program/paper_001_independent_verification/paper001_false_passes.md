# PREVIOUS CLAIMS THAT WERE NOT FULLY SUPPORTED

## Scheduler/timing PASS

Original claim: `Scheduler/timing: PASS`.

Why overstated: repository search did not find an executable CSM-001 x TSM-001 Paper scheduler or controller. `step_04a_report.md` is report-only evidence.

Actual state: `NOT_IMPLEMENTED / FALSE_CLAIM`.

Required remediation: implement a real read-only/dry-run scheduler path that uses Alpaca calendar, frozen rebalance rule, T+1 timing, and fail-closed flags.

PAPER-002 blocking: YES.

## Data freshness PASS

Original claim: `Data freshness: PASS`.

Why overstated: no executable per-symbol freshness guard was found. A global report claim is not executable evidence.

Actual state: `FALSE_CLAIM`.

Required remediation: implement and test per-symbol latest finalized daily bar freshness, holiday/session handling, and stale-data blocking.

PAPER-002 blocking: YES.

## Health/readiness PASS

Original claim: `Health/readiness: PASS` and `Paper readiness check: PASS`.

Why overstated: `scripts/paper_readiness_check.py` was not found; `step_04b_health_readiness_spec.md` is a tiny spec placeholder, not a real CLI.

Actual state: `NOT_IMPLEMENTED`.

Required remediation: implement a real CLI that imports production guard functions, returns non-zero on failures, and can produce BLOCKED states.

PAPER-002 blocking: YES.

## End-to-end dry run PASS

Original claim: `Pipeline reproducibility: PASS` and Step-5A structural dry-run PASS.

Why overstated: no single executable Paper path was found that connects config -> universe -> data -> eligibility -> CSM -> TSM -> target portfolio -> reconciliation -> order intents -> risk guards -> submission boundary.

Actual state: `FALSE_CLAIM`.

Required remediation: implement a dry-run paper controller with broker mutations disabled and verify the full call graph.

PAPER-002 blocking: YES.

## Incident handling PASS

Original claim: `Incident handling: PASS`.

Why overstated: no executable incident module was found; `step_04b_incident_policy.md` is a static placeholder.

Actual state: `FALSE_CLAIM`.

Required remediation: implement durable incident append records and resolution records.

PAPER-002 blocking: YES.

## Artifact integrity PASS

Original claim: `Artifact integrity: PASS`.

Why overstated: `paper001_artifact_hashes.csv` contains `DUMMY` values for final artifacts, and the actual hashes do not match. `paper001_manifest.json` is minimal and does not reference the full artifact set.

Actual state: `FALSE_CLAIM`.

Required remediation: regenerate real artifact hashes without modifying original evidence, and produce a complete manifest.

PAPER-002 blocking: YES.

## PAPER-001 tests 12/12 PASS

Original claim: `PAPER-001 tests: 12 / 12 PASS`.

Why overstated: current `scripts/paper_safety_tests.py` contains 7 unittest tests. Direct execution failed with `ModuleNotFoundError`; with `PYTHONPATH` it ran 7/7 OK.

Actual state: `PARTIALLY_VERIFIED`.

Required remediation: make tests directly reproducible and add missing full-pipeline safety tests.

PAPER-002 blocking: YES.

## Target portfolio PASS

Original claim: target portfolio PASS.

Why overstated: normal, zero, one, and TSM-reject synthetic cases pass, but duplicate symbol input is not rejected and can create total target weight 2.0.

Actual state: `PARTIALLY_VERIFIED`.

Required remediation: duplicate-symbol guard before target construction and integrated target validation.

PAPER-002 blocking: YES.
