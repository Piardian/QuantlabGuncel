# CPP-001 Data Inventory & Alignment Audit

## Purpose

CPP-001 audits whether the eight frozen construct outputs are available, alignable, and sample-size eligible for the preregistered CPP comparison stages.

This stage does not compute statistical construct relationships.

## Frozen Constructs Audited

| construct_id | construct_name | frozen_output_path | cpp_alignment_column | file_exists |
| --- | --- | --- | --- | --- |
| MR-001 | Market Regime | output\mr_001_validation\mr001_regime_output.csv | posterior_state_0 | True |
| LIQ-001 | Market Liquidity | output\liq_001_validation\liq001_liquidity_output.csv | liq001_zscore | True |
| VOL-001 | Volatility State | output\vol_001_validation\vol001_volatility_output.csv | vol001_zscore | True |
| BRD-001 | Market Breadth | output\brd001_breadth_state.csv | brd001_zscore | True |
| COR-001 | Market Correlation | output\cor001_correlation_state.csv | cor001_zscore_252d | True |
| CRD-001 | Credit Stress | output\crd_001_validation\crd001_credit_stress_output.csv | crd001_zscore_252d | True |
| FUND-001 | Funding Spread | output\fund_001_validation\fund001_funding_stress_output.csv | fund001_zscore_252d | True |
| OPT-001 | Options-Implied Volatility | output\opt_001_validation\opt001_options_implied_output.csv | opt001_zscore_252d | True |

## Date Coverage Summary

| construct_id | rows | first_date | last_date | alignment_valid_observations | first_alignment_date | last_alignment_date |
| --- | --- | --- | --- | --- | --- | --- |
| MR-001 | 4509 | 2008-01-31 | 2025-12-31 | 4509 | 2008-01-31 | 2025-12-31 |
| LIQ-001 | 4023 | 2010-01-05 | 2025-12-31 | 3753 | 2011-01-31 | 2025-12-31 |
| VOL-001 | 4024 | 2010-01-04 | 2025-12-31 | 3753 | 2011-01-31 | 2025-12-31 |
| BRD-001 | 4023 | 2010-01-04 | 2025-12-30 | 3573 | 2011-10-14 | 2025-12-30 |
| COR-001 | 4023 | 2010-01-04 | 2025-12-30 | 3712 | 2011-03-29 | 2025-12-30 |
| CRD-001 | 781 | 2023-07-31 | 2026-07-27 | 530 | 2024-07-16 | 2026-07-27 |
| FUND-001 | 18931 | 1954-01-04 | 2026-07-27 | 6463 | 1998-01-05 | 2026-07-27 |
| OPT-001 | 9541 | 1990-01-02 | 2026-07-28 | 8988 | 1990-12-28 | 2026-07-28 |

## Common Sample Result

The exact-date common sample across all eight CPP alignment columns contains **188** valid observations from **2024-07-22** through **2025-12-30**.

## Pairwise Readiness

The minimum pairwise exact-date overlap is **262** observations. The preregistered pairwise minimum is **252** observations.

## Multivariate Readiness

The preregistered multivariate/common-sample minimum is **756** observations. The current common sample is **188**, so multivariate stages are **NOT_ELIGIBLE** by sample-size rule.

## Boundary

CPP-001 reports availability, coverage, missingness, and eligibility only. It does not infer overlap in information content, redundancy, orthogonality, complementarity, lead-lag structure, causality, predictive value, or economic utility.
