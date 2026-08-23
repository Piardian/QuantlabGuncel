# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

BRD-001

Implementation Development & Verification

IM-001

--------------------------------------------------

BACKGROUND

--------------------------------------------------

BRD-001 has completed:

Completed: RP-001 Research Prioritization

Completed: LR-001 Literature Review

Completed: CD-001 Construct Definition

CD-001 froze the official construct:

US Equity 200-Day Moving-Average Breadth State

Definition:

Percentage of eligible securities in `sp500_current_universe.csv` whose adjusted close is above their own trailing 200-day simple moving average.

--------------------------------------------------

PURPOSE

--------------------------------------------------

Develop and verify a complete implementation of BRD-001 that faithfully reproduces the construct frozen in CD-001.

The objective is implementation fidelity.

NOT predictive performance.

NOT trading performance.

--------------------------------------------------

IMPLEMENTATION REQUIREMENTS

--------------------------------------------------

Inputs:

- `sp500_current_universe.csv`
- daily adjusted or normalized close for every ticker

Model:

- rolling 200-day simple moving average per security
- binary above-SMA200 participation flag per security
- daily market-level percentage above SMA200
- 252-day z-score and percentile normalization
- coverage diagnostics

Outputs:

- `date`
- `brd001_pct_above_sma200`
- `brd001_zscore`
- `brd001_percentile`
- `brd001_count_above_sma200`
- `brd001_count_not_above_sma200`
- `brd001_eligible_count`
- `brd001_total_universe_count`
- `brd001_coverage_ratio`
- `brd001_valid_observation`

--------------------------------------------------

IMPLEMENTATION RULES

--------------------------------------------------

The implementation must be:

- deterministic
- reproducible
- modular
- fully documented
- independently executable

Every parameter must originate from CD-001.

No undocumented assumptions are permitted.

--------------------------------------------------

VERIFICATION REQUIREMENTS

--------------------------------------------------

Verify:

- universe loading
- ticker sorting
- close data loading
- SMA200 calculation
- eligibility rules
- daily market aggregation
- z-score calculation
- percentile calculation
- coverage diagnostics
- output serialization
- deterministic re-run hash

--------------------------------------------------

FORBIDDEN

--------------------------------------------------

Do NOT:

- Run trading backtests.
- Optimize thresholds.
- Change the moving-average window.
- Change the normalization window.
- Add new variables.
- Modify CD-001.
- Evaluate predictive validity.
- Evaluate economic value.
- Claim trading edge.

--------------------------------------------------

EXPECTED OUTPUTS

--------------------------------------------------

Generate:

brd001_breadth_pipeline.py

config.yaml

implementation_specification.md

verification_report.md

reproducibility_report.md

unit_test_report.md

execution_example.md

limitations.md

executive_summary.md

--------------------------------------------------

SUCCESS CRITERIA

--------------------------------------------------

IM-001 is successful only if:

- Every component required by CD-001 exists.
- Every component faithfully implements CD-001.
- Independent execution reproduces identical outputs.
- The implementation is fully documented.
- The construct is ready for empirical validation.

The study may conclude only:

- Successfully implemented
- Partially implemented
- Implementation mismatch
- Implementation incomplete

No statements regarding predictive validity, trading performance, alpha generation, or economic value are permitted.

Successful completion of IM-001 authorizes progression to:

BRD-001 / CV-001 Construct Validation.

