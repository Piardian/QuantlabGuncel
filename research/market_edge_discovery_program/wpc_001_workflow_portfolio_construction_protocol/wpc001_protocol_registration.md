# WPC-001: Workflow Portfolio Construction Protocol

## Background

WRS-001 classified the CSM-001 x TSM-001 UC-3 workflow as:

**Research-Validated Workflow, Not Production Ready**

The next unresolved question is how the workflow should be translated into a fixed, auditable research portfolio process.

## Purpose

WPC-001 registers the portfolio construction protocol for the UC-3 workflow.

No empirical portfolio analysis is performed in this stage.

## Primary Research Question

Can the UC-3 workflow be converted into a deterministic research portfolio process with fixed, reproducible accounting rules?

## Scope

Evaluate only:

**UC-3: CSM leadership subset inside TSM_HIGH**

The benchmark remains:

**TSM-positive non-CSM region**

## Portfolio Construction Rules

Portfolio type:

- Long-only
- Equal-weight
- Fully systematic
- No discretionary overrides

Eligible holdings:

- `csm001_top_decile_flag == True`
- `tsm001_positive_state == True`
- both constructs must be valid

Benchmark holdings:

- `csm001_top_decile_flag == False`
- `tsm001_positive_state == True`
- both constructs must be valid

## Rebalance Schedule

Registered rebalance frequency:

- Monthly

Rebalance date:

- First available trading day of each calendar month

## Holding Period

Registered holding period:

- One month until next rebalance

No overlapping sleeves are permitted in WPC-002.

## Position Weighting

Registered weighting:

- Equal-weight across selected holdings

No volatility weighting, score weighting, rank weighting or optimization is permitted.

## Cash Handling

If no holdings are available on a rebalance date:

- portfolio holds cash
- cash return is assumed to be 0%

## Position Count Policy

No max position limit is imposed in WPC-002.

Position count is measured, not optimized.

## Transaction Timing

Registered timing:

- Signals are formed using data available at rebalance close.
- Portfolio return is measured from next trading day close to next rebalance close.

This rule is intended to avoid same-close execution assumptions.

## Forbidden

Do NOT:

- optimize rebalance frequency
- optimize position count
- optimize weights
- tune holding period
- modify CSM-001
- modify TSM-001
- add risk management overlays
- add stop losses
- add discretionary filters
- recommend production deployment

## Authorized Next Stage

**WPC-002: Workflow Portfolio Construction Validation**
