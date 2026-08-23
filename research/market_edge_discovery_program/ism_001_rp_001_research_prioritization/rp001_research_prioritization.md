# ISM-001 / RP-001 Research Prioritization

## Purpose

Determine whether Industry Momentum should be accepted as an independent scientific edge construct worthy of full investigation within the Market Edge Discovery Program.

This stage does not define the construct, choose industry taxonomy, select lookback windows, implement code, backtest, optimize or claim alpha.

## Primary Research Question

Should Industry Momentum be accepted as an independent scientific construct worthy of full investigation?

## Decision

**GO**

## Rationale

Industry Momentum is a scientifically important edge-mechanism candidate because the literature directly studies whether industry-level return persistence explains part of individual stock momentum.

The seminal motivation comes from Moskowitz and Grinblatt's "Do Industries Explain Momentum?", which documents a strong industry component in momentum effects. Related information-diffusion literature, including Hou's industry lead-lag work, provides an independent theoretical channel: information may diffuse gradually within or across industries.

The GO decision is based on scientific relevance, literature maturity, construct independence, and high expected research value.

The decision is not based on expected profitability, production suitability, or implementation convenience.

## Scientific Assessment

| dimension | assessment | rationale |
|---|---|---|
| Scientific importance | HIGH | Industry momentum directly addresses whether return persistence is partly industry-level rather than purely firm-specific. |
| Historical development | HIGH | The construct has a clear academic origin in late-1990s momentum literature and later information-diffusion work. |
| Academic maturity | MODERATE-HIGH | Seminal papers, follow-up studies and practitioner references exist, though exact taxonomy and implementation details vary. |
| Independent motivation | HIGH | ISM is distinct from CSM, TSM and RSM because the unit of signal formation is an industry group rather than an individual security alone. |
| Practical relevance | HIGH | Industry grouping, sector rotation, industry leadership and lead-lag effects are widely used in practitioner research and portfolio diagnostics. |
| Relationship to existing validated risk constructs | DISTINCT_BUT_REQUIRES_MAPPING | ISM is an edge-mechanism candidate; future CPP-style work may compare it with breadth, correlation, volatility and regime constructs. |
| Expected incremental research value | HIGH | ISM can test whether momentum information concentrates at the group/industry layer after CSM, TSM and RSM evidence. |
| Availability of high-quality literature | MODERATE-HIGH | Foundational and follow-up papers exist; LR-001 should separate academic consensus from practitioner sector-rotation claims. |
| Availability of public datasets | MODERATE | Price data is available, but reproducible industry classification and historical industry membership are major data-quality risks. |
| Suitability for rule-based construct development | MODERATE-HIGH | Industry ranking can be deterministic once taxonomy, weighting and membership rules are frozen in CD-001. |

## Critical Qualification

ISM-001 has a higher taxonomy/data-integrity risk than raw price momentum constructs.

Before CD-001 freezes the construct, the program must explicitly resolve:

- Which industry taxonomy is used.
- Whether classifications are current or point-in-time.
- Whether industry returns are equal-weighted or value-weighted.
- Whether industry membership is static or historical.
- How single-stock or thin industries are handled.
- Whether the construct ranks industries, stocks by industry score, or both.
- How survivorship bias is controlled or disclosed.

## Evidence Classification

Supported by evidence:

- Industry Momentum is a recognized academic construct.
- It is conceptually distinct from individual-stock cross-sectional momentum.
- It has a plausible information-diffusion mechanism.
- It is scientifically important after CSM, TSM and RSM.

Partially supported:

- Implementation feasibility is reasonable if industry taxonomy and membership policy are frozen.

Not supported at RP stage:

- Any claim of predictive validity in this repository.
- Any claim that ISM is superior to CSM, TSM or RSM.
- Any production readiness conclusion.
- Any economic utility claim.

## Final RP-001 Conclusion

ISM-001 receives a **GO** decision for literature review.

The next stage is:

**ISM-001 / LR-001**

## Sources Used

- Moskowitz and Grinblatt, "Do Industries Explain Momentum?"
- Hou, "Industry Information Diffusion and the Lead-Lag Effect in Stock Returns"
- Hong, Torous and Valkanov, "Do Industries Lead the Stock Market?"

