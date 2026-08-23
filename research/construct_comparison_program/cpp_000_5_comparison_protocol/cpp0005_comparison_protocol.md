# CPP-000.5: Comparison Protocol Registration

## Scope

This stage freezes the comparison protocol before any statistical analysis begins.

No construct outputs were aligned, inspected, compared, modeled, or statistically analyzed during CPP-000.5.

## Primary Comparison Questions

1. How much information overlap exists between validated constructs?
2. Which constructs provide incremental information beyond others?
3. Which constructs are redundant, partially redundant, orthogonal, complementary, upstream candidates, or downstream candidates?
4. What multivariate information architecture best describes the frozen construct ecosystem?
5. Which conclusions remain stable under preregistered robustness checks?

## Confirmatory Analysis Registry

| analysis_id | phase | analysis_name | type | primary_question | methods | minimum_sample | multiple_testing | output |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | CPP-001 | Data Inventory and Alignment Audit | confirmatory | Are frozen construct outputs available and alignable for valid comparison? | coverage audit; missingness audit; overlap matrix; date frequency audit | At least 252 aligned observations for pairwise eligibility | Not applicable; descriptive audit only | data_alignment_report |
| A2 | CPP-002 | Pairwise Linear Dependence | confirmatory | How strongly do construct pairs co-move linearly? | Pearson correlation on standardized construct outputs | N >= 252 pairwise aligned observations | Benjamini-Hochberg FDR q=0.05 across pairwise tests | pairwise_dependence_matrix |
| A3 | CPP-002 | Pairwise Rank Dependence | confirmatory | How strongly do construct pairs co-move monotonically? | Spearman rank correlation; Kendall tau if feasible | N >= 252 pairwise aligned observations | Benjamini-Hochberg FDR q=0.05 across pairwise tests | rank_dependence_matrix |
| A4 | CPP-002 | Nonlinear Dependence | confirmatory | Do construct pairs share nonlinear information? | mutual information estimator; distance correlation where implementable without changing construct outputs | N >= 504 pairwise aligned observations | Benjamini-Hochberg FDR q=0.05 across pairwise tests | nonlinear_dependence_matrix |
| A5 | CPP-003 | Incremental Information | confirmatory | Does each construct add information beyond the rest? | nested regression/log-loss/R2 delta depending on preregistered target family; partial correlation; conditional mutual information | N >= 756 common aligned observations for multivariate eligibility | FDR q=0.05 within target family | incremental_information_matrix |
| A6 | CPP-003.5 | Robustness and Sensitivity | confirmatory | Are information relationships stable across samples and periods? | rolling windows; year blocks; crisis/calm blocks; common-sample vs maximum-pairwise-sample; bootstrap CI | N >= 252 per tested subperiod; otherwise inconclusive | Report corrected and uncorrected; conclusions require corrected stability | robustness_report |
| A7 | CPP-004 | Redundancy and Orthogonality Classification | confirmatory | Which constructs are redundant, partially redundant, orthogonal, or inconclusive? | thresholded dependence; partial dependence; stability requirements; VIF/PCA diagnostics | Must pass CPP-001 eligibility | Uses corrected CPP-002/CPP-003 outputs only | redundancy_orthogonality_matrix |
| A8 | CPP-005 | Complementarity and Multivariate Information | confirmatory | Which construct combinations provide complementary information? | multivariate nested comparisons; group ablation on frozen outputs; PCA/factor loading; conditional information gain | N >= 756 common aligned observations | FDR q=0.05 within predefined construct groups | multivariate_information_report |
| A9 | CPP-006 | Lead-Lag Temporal Association | confirmatory | Do constructs systematically lead or lag each other temporally? | cross-correlation at lags [-60,-20,-5,0,5,20,60]; lagged regression association; Granger-style association if sample permits | N >= 756 aligned observations after lagging | FDR q=0.05 by construct-pair lag family | lead_lag_map |
| A10 | CPP-007 | Information Architecture Synthesis | synthesis | How should the validated construct ecosystem be scientifically organized? | evidence-weighted taxonomy from CPP-002 through CPP-006 | Uses prior eligible outputs | Not applicable; synthesis only | construct_information_matrix |
| A11 | CPP-007.5 | Scientific Interpretation Review | quality_control | Are conclusions appropriately bounded by evidence? | overclaim audit; causal-language audit; literature-consistency review; conflict review | Not applicable | Not applicable | interpretation_review |
| A12 | CPP-008 | Final Construct Ecosystem Review | synthesis | What is the final evidence-supported construct ecosystem architecture? | final evidence synthesis; construct information matrix; limitations; future work | Uses all completed CPP evidence | Not applicable | final_ecosystem_review |

## Global Statistical Standards

- Primary significance level: `alpha = 0.05`.
- Primary multiple-comparison correction: Benjamini-Hochberg FDR at `q = 0.05`.
- Minimum pairwise sample: `N >= 252` aligned observations.
- Minimum multivariate sample: `N >= 756` common aligned observations.
- Confirmatory conclusions require corrected significance where hypothesis tests are used and directional stability in robustness checks.
- Exploratory analyses must be labeled as exploratory and cannot alter confirmatory conclusions.

## Locked Interpretation Boundary

CPP may identify information overlap, redundancy, complementarity, orthogonality, and temporal association.

CPP may not infer trading edge, profitability, production recommendations, or causality.
