# /goal

# RESEARCH PROGRAM

Market Signal Discovery Program

Version 3.0

Construct ID

OPT-001

Implementation Development & Verification

IM-001

--------------------------------------------------

## BACKGROUND

OPT-001 has completed:

- RP-001 Research Prioritization
- LR-001 Literature Review
- CD-001 Construct Definition

The construct is now frozen as:

```text
US Equity Index Option-Implied Volatility State
```

Frozen source:

```text
VIXCLS
```

No construct modifications are permitted during IM-001.

--------------------------------------------------

## PURPOSE

Develop and verify a deterministic implementation of OPT-001 that faithfully reproduces the frozen CD-001 specification.

The objective is implementation fidelity.

Not predictive performance.

Not trading performance.

--------------------------------------------------

## IMPLEMENTATION REQUIREMENTS

Inputs:

- `VIXCLS`

Derived variables:

- raw VIX close
- 252-valid-observation z-score
- 252-valid-observation percentile
- valid observation count
- data quality flag

Rules:

- no forward filling in official construct values
- raw values require positive VIXCLS
- normalized outputs require 252 valid observations
- deterministic output

--------------------------------------------------

## EXPECTED OUTPUTS

Generate:

- `opt001_options_implied_model.py`
- `feature_pipeline.py`
- `config.yaml`
- `implementation_specification.md`
- `verification_report.md`
- `reproducibility_report.md`
- `unit_test_report.md`
- `execution_example.md`
- `limitations.md`
- `executive_summary.md`

--------------------------------------------------

## VERIFICATION REQUIREMENTS

Verify:

- input loading
- date parsing
- missing-data handling
- non-positive input handling
- rolling z-score calculation
- rolling percentile calculation
- output schema
- deterministic regeneration

--------------------------------------------------

## FORBIDDEN

Do NOT:

- modify CD-001
- change source series
- change normalization window
- forward fill official construct values
- run trading backtests
- evaluate prediction
- evaluate economic value
- claim alpha or trading utility

--------------------------------------------------

## SUCCESS CRITERIA

IM-001 is successful only if:

- every component required by CD-001 exists,
- the implementation faithfully reproduces CD-001,
- independent execution can regenerate identical outputs,
- verification artifacts are produced,
- no predictive or economic claims are made.

Successful completion authorizes progression to:

```text
OPT-001 / CV-001
```

