# DVB-001 Budget Tiers

## Tier 1 — Minimum Viable Research Stack

## Purpose

Start formal prospective US equity capture at the lowest realistic cost while preserving scientific minimum standards.

## Required Capabilities

- daily OHLCV
- NYSE, Nasdaq, NYSE American support
- common-stock distinguishability
- stable security identity or robust internal fallback
- ticker/lifecycle tracking
- split/dividend support
- local storage permission
- automated retrieval permission
- prospective first-seen capture permission

## Candidate Shape

Likely one lower-cost market-data API plus either:

- built-in reference/corporate-action data, or
- a second source for lifecycle/security master.

## Scientific Risk

Tier 1 may remain insufficient if lifecycle, delisting, permanent identifier, or license terms are weak.

## Tier 2 — Professional Research Stack

## Purpose

Increase probability of passing SLA-002 and PDC refreeze with better identifier, lifecycle, and corporate-action semantics.

## Required Capabilities

Everything in Tier 1, plus:

- stronger security master
- permanent/security-level identifiers
- fuller corporate-action event semantics
- clearer business/internal research license
- better support and operational reliability

## Candidate Shape

Likely Databento, Sharadar/Nasdaq Data Link, Norgate higher-tier, or multi-source combination.

## Scientific Risk

Higher cost and licensing complexity, but lower scientific ambiguity.

## Tier 3 — Institutional Stack

## Purpose

Maximize historical and survivorship-aware research quality.

## Candidate Shape

WRDS / CRSP / Compustat-style institutional data stack.

## Scientific Risk

May be economically or access constrained. It should not be required as the initial condition unless the owner has institutional access and budget.

