# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

COR-001

Implementation Development & Verification

IM-001

--------------------------------------------------

BACKGROUND

--------------------------------------------------

COR-001 has completed:

Completed: RP-001

Completed: LR-001

Completed: CD-001

CD-001 froze the official construct:

US Equity Market Average Pairwise Correlation State

Definition:

Average pairwise Pearson correlation of daily log returns across a fixed US equity universe over a trailing 60-trading-day window, with trailing 252-valid-observation z-score and percentile normalization.

--------------------------------------------------

PURPOSE

--------------------------------------------------

Develop and verify a deterministic implementation of the frozen COR-001 construct.

The objective is implementation fidelity.

Not predictive performance.

Not trading performance.

Not economic value.

--------------------------------------------------

IMPLEMENTATION REQUIREMENTS

--------------------------------------------------

The implementation MUST exactly follow CD-001.

Inputs:

- fixed US equity universe
- daily adjusted or normalized close prices

Derived variables:

- daily log returns
- rolling 60-day return matrix
- pairwise Pearson correlation matrix
- average off-diagonal pairwise correlation
- 252-day z-score
- 252-day percentile

Outputs:

- cor001_avg_pairwise_corr_60d
- cor001_zscore_252d
- cor001_percentile_252d
- cor001_eligible_security_count
- cor001_pair_count
- cor001_coverage_ratio

--------------------------------------------------

IMPLEMENTATION RULES

--------------------------------------------------

The implementation must be:

- deterministic
- reproducible
- modular
- documented
- independently executable

Every parameter must originate from CD-001.

No undocumented assumptions are permitted.

--------------------------------------------------

VERIFICATION REQUIREMENTS

--------------------------------------------------

Verify:

- universe loading
- price loading
- log return calculation
- rolling eligibility logic
- correlation matrix calculation
- off-diagonal aggregation
- normalization calculation
- coverage diagnostics
- output serialization
- deterministic execution

--------------------------------------------------

FORBIDDEN

--------------------------------------------------

Do NOT:

- run trading backtests
- optimize parameters
- tune windows
- change the universe after observing results
- change estimator type
- introduce additional variables
- evaluate predictive validity
- evaluate economic value
- claim trading edge

--------------------------------------------------

EXPECTED OUTPUTS

--------------------------------------------------

Generate:

- cor001_correlation_pipeline.py
- config.yaml
- verify_cor001.py
- implementation_specification.md
- verification_report.md
- reproducibility_report.md
- unit_test_report.md
- execution_example.md
- limitations.md
- executive_summary.md

--------------------------------------------------

SUCCESS CRITERIA

--------------------------------------------------

IM-001 is successful only if:

- every component required by CD-001 exists
- every component faithfully implements CD-001
- independent execution reproduces identical outputs
- the implementation is fully documented
- the construct is ready for empirical validation

The study may conclude only:

- Successfully implemented
- Partially implemented
- Implementation mismatch
- Implementation incomplete

No statements regarding predictive validity, trading performance, alpha generation, or economic value are permitted.

