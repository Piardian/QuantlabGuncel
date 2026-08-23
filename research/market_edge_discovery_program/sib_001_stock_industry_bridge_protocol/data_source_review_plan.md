# Data Source Review Plan

## Purpose

Define how SIB-002 should evaluate candidate data sources.

## Evaluation Dimensions

Every source should be reviewed for:

- point-in-time availability
- coverage period
- US equity coverage
- identifier quality
- ticker and delisting handling
- taxonomy type
- compatibility with Ken French 49 industries
- reproducibility
- licensing constraints
- cost/access constraints
- auditability

## Candidate Source Categories

SIB-002 may evaluate:

- academic datasets
- CRSP/Compustat-style security master data
- historical SIC/NAICS files
- point-in-time GICS files
- Ken French assignment-compatible sources
- other documented point-in-time taxonomies

## Output Expected From SIB-002

SIB-002 should end with exactly one of:

- GO: A suitable bridge source exists.
- CONDITIONAL GO: A source may work but constraints remain.
- NO GO: No scientifically valid source is available.
