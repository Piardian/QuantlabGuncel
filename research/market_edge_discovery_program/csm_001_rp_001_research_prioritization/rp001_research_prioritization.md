# CSM-001 / RP-001 Research Prioritization Report

## Primary Research Question

Should Cross-Sectional Momentum be accepted as an independent scientific construct worthy of full investigation?

## Decision

```text
GO
```

## Scientific Assessment

| dimension | assessment | rationale |
| --- | --- | --- |
| Scientific importance | HIGH | Cross-sectional momentum is one of the central empirical regularities in asset pricing and appears in seminal factor-model and anomaly literature. |
| Historical development | HIGH | The mechanism has a long research history beginning with foundational relative-strength portfolio evidence and later integration into factor-model and international literature. |
| Academic maturity | HIGH | The literature contains seminal papers, international tests, practitioner variants, open replication resources, and critical meta-research. |
| Independent motivation | HIGH | The construct is motivated independently of the existing production strategy and validated risk constructs. |
| Practical relevance | HIGH | Momentum appears in factor models, portfolio construction, practitioner index design, and academic anomaly datasets, while carrying known implementation risks. |
| Relationship to existing validated risk constructs | DISTINCT_BUT_UNPROVEN_INCREMENTAL | CSM is an edge-mechanism candidate rather than a risk-state sensor. CPP did not establish incremental relation versus existing risk constructs, so independence remains future work. |
| Expected incremental research value | HIGH | The construct can test whether the MEDP can move from risk-state sensors to a canonical edge-mechanism construct using strict scientific gates. |
| Availability of high-quality literature | HIGH | Multiple seminal, replication, international, and skeptical/meta-research sources are available. |
| Availability of public datasets | HIGH | Price-based cross-sectional returns can be reconstructed from public market data, and Open Asset Pricing provides replicated academic signals/test assets. |
| Suitability for rule-based construct development | HIGH | Cross-sectional ranking/sorting constructs can be specified deterministically, although exact definition must be frozen later in CD, not RP. |

## Literature Availability

| source_id | citation | role | url |
| --- | --- | --- | --- |
| JT1993 | Jegadeesh & Titman (1993), Returns to Buying Winners and Selling Losers | Foundational U.S. equity cross-sectional momentum evidence | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1993.tb04702.x |
| CARHART1997 | Carhart (1997), On Persistence in Mutual Fund Performance | Introduces/uses momentum as fourth factor in mutual fund performance context | https://ideas.repec.org/a/bla/jfinan/v52y1997i1p57-82.html |
| AMP2013 | Asness, Moskowitz & Pedersen (2013), Value and Momentum Everywhere | Cross-market evidence and common factor structure | https://onlinelibrary.wiley.com/doi/10.1111/jofi.12021 |
| FF2012 | Fama & French (2012), Size, Value, and Momentum in International Stock Returns | International equity evidence and regional qualifications | https://ideas.repec.org/a/eee/jfinec/v105y2012i3p457-472.html |
| OAP2022 | Chen & Zimmermann (2022), Open Source Cross-Sectional Asset Pricing | Open replication/data/code ecosystem for cross-sectional predictors | https://www.openassetpricing.com/ |
| HLZ2016 | Harvey, Liu & Zhu (2016), ...and the Cross-Section of Expected Returns | Multiple-testing and false-discovery discipline for factor research | https://academic.oup.com/rfs/article/29/1/5/1843824 |
| MP2016 | McLean & Pontiff (2016), Does Academic Research Destroy Stock Return Predictability? | Out-of-sample and post-publication decay risk | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623 |
| LR001 | Project LR-001 Momentum and Relative Strength Literature Review | Existing internal synthesis: canonical cross-sectional momentum has strongest academic support in momentum family | research/literature_reviews/lr_001/executive_summary.md |
| CPP008 | CPP-008 Final Construct Ecosystem Review | Existing validated risk construct ecosystem limitation: only limited pairwise architecture, no full incremental map | research/construct_comparison_program/cpp_008_final_construct_ecosystem_review/executive_summary.md |

## Existing Construct Relationship Assessment

| existing_construct | relationship | status | note |
| --- | --- | --- | --- |
| MR-001 | Potential regime interaction / crash-risk context | PLAUSIBLE_BUT_UNTESTED | Momentum crash/regime sensitivity literature motivates later interaction questions, not RP conclusions. |
| VOL-001 | Potential volatility-state conditioning or risk-management context | PLAUSIBLE_BUT_UNTESTED | Momentum implementation risk may vary with volatility; no MEDP predictive/economic claim yet. |
| BRD-001 | Possible market-participation context | UNKNOWN | No completed CPP evidence establishes incremental relation. |
| LIQ-001 | Potential liquidity/capacity/cost relevance | PLAUSIBLE_BUT_UNTESTED | Liquidity concerns are central implementation risks; not a reason to reject prioritization. |
| COR-001 | Potential common-risk / crowding environment context | UNKNOWN | No completed CPP evidence establishes a mechanism. |
| CRD-001 | Potential stress environment context | UNKNOWN | No completed CPP evidence establishes relation. |
| FUND-001 | Potential funding-stress context | UNKNOWN | No completed CPP evidence establishes relation. |
| OPT-001 | Potential option-implied risk/crash context | PLAUSIBLE_BUT_UNTESTED | Future studies may test interaction after CSM lifecycle reaches eligible stages. |

## Research Gaps

| gap | importance | phase_to_address | note |
| --- | --- | --- | --- |
| Operational definition not yet frozen | HIGH | CD-001 | RP cannot choose lookback, skip-month convention, ranking universe, weighting, rebalance, or long-only adaptation. |
| Long-only versus canonical long-short distinction | HIGH | LR-001 / CD-001 | Academic evidence often uses long-short winner-minus-loser portfolios; MEDP must avoid importing claims into a different long-only construct without validation. |
| Crash and regime sensitivity | HIGH | LR-001 onward | Momentum crash risk is a known limitation and must be part of later literature and validation planning. |
| Transaction costs, turnover, capacity | HIGH | EV-001 | Economic usefulness cannot be inferred from predictive or literature evidence alone. |
| Data quality and survivorship | HIGH | CD-001 / IM-001 | Universe construction and historical constituent handling must be specified before empirical validation. |
| Incremental value versus risk constructs | MEDIUM | Later CPP/MEDP integration | CPP current status is limited pairwise architecture only, so incremental relation is unknown. |

## Risk / Limitation Register

| risk | severity | control |
| --- | --- | --- |
| Popularity bias | MEDIUM | RP decision uses evidence maturity and constructability, not popularity or historical performance alone. |
| Parameter fishing later | HIGH | RP explicitly forbids lookback/ranking/parameter selection; CD must freeze definitions before validation. |
| Long-short literature overgeneralized to long-only construct | HIGH | LR-001 must separate canonical evidence from any future long-only operationalization. |
| Data snooping / factor zoo risk | HIGH | Harvey-Liu-Zhu and McLean-Pontiff style skepticism must be embedded in later validation standards. |
| Implementation data leakage | HIGH | Point-in-time universe, delisting, corporate actions, and decision-date availability must be handled in CD/IM. |

## Conclusion

Cross-Sectional Momentum is sufficiently important, mature, independently motivated, and constructable to justify entering the full Market Edge Discovery Program lifecycle.

## Interpretation Boundary

RP-001 does not define indicators, choose lookbacks, choose ranking methodology, evaluate predictive power, perform backtests, claim alpha, or recommend production deployment.
