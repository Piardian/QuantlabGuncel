# DM-001 / RP-001 Research Prioritization

## Purpose

Determine whether Dual Momentum should be accepted as an independent scientific Edge Construct worthy of a full Market Edge Discovery Program lifecycle.

RP-001 does not define indicators, choose lookbacks, select benchmarks, implement code, run backtests, evaluate profitability or claim alpha.

## Primary Research Question

Should Dual Momentum be accepted as an independent scientific Edge Construct worthy of full scientific investigation?

## Decision

**NO-GO**

## Decision Basis

Dual Momentum is scientifically relevant and practically prominent, but the accumulated evidence does not establish it as an independent mechanism distinct from the already completed CSM-001 and TSM-001 constructs.

The literature generally operationalizes Dual Momentum as a combination or sequence of:

- Relative or cross-sectional momentum, which selects comparatively stronger assets.
- Absolute or time-series momentum, which conditions exposure on an asset's own prior return or trend state.

Those two information sources already have completed, frozen research lifecycles in this repository. Direct Dual Momentum studies support investigating their combination, but they do not provide a sufficiently distinct theoretical mechanism to justify registering the combination as a new independent construct at RP-001.

## Scientific Assessment

| Dimension | Assessment | Rationale |
| --- | --- | --- |
| Scientific importance | Moderate-High | Combining relative selection with absolute trend conditioning is an important portfolio-research question. |
| Historical development | Moderate | The Dual Momentum label is newer and more practitioner-led than the foundational CSM and TSM literatures. |
| Academic maturity | Moderate | Peer-reviewed direct studies exist, but the dedicated evidence base is substantially narrower than the component literatures. |
| Theoretical motivation | Moderate | Behavioral underreaction and trend persistence motivate the components; a separate Dual Momentum mechanism is not clearly established. |
| Practical relevance | High | Dual Momentum is widely discussed as a transparent tactical allocation framework. |
| Construct independence | Low | The observable rule is explicitly composed of relative/cross-sectional and absolute/time-series momentum. |
| Relationship to CSM-001 | Direct component | Relative ranking or winner selection is the cross-sectional component. |
| Relationship to TSM-001 | Direct component | Absolute momentum or own-history trend conditioning is the time-series component. |
| Relationship to ISM-001 | Possible implementation layer | Industry or asset-class selection can supply a ranked universe, but this is an implementation choice rather than a distinct Dual Momentum mechanism. |
| Expected incremental information | Moderate but unproven | Complementarity may exist, but that is an interaction question and not evidence of construct independence. |
| Public OHLCV availability | High | Lagged price returns can be reconstructed from public data if a later comparison study is preregistered. |
| Rule-based constructability | High | A relative rank followed by an absolute condition can be represented deterministically once choices are frozen. |
| Reproducibility potential | High | Reproducibility is feasible, but many universe, benchmark and fallback-asset choices must be preregistered. |

## Literature Evidence

### Component Foundations

- [Jegadeesh and Titman (1993)](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x) establish the foundational cross-sectional winner-minus-loser momentum evidence.
- [Moskowitz, Ooi and Pedersen (2012)](https://doi.org/10.1016/j.jfineco.2011.11.003) distinguish time-series momentum from cross-sectional momentum and document that the two are related but not identical.
- [Asness, Moskowitz and Pedersen (2013)](https://doi.org/10.1111/jofi.12021) provide broad cross-market evidence for momentum and a common factor structure.

### Direct Dual Momentum Literature

- [Antonacci, Risk Premia Harvesting Through Dual Momentum](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2042750) explicitly combines relative and absolute momentum and is the principal practitioner-origin reference.
- [Lim, Wang and Yao (2018)](https://doi.org/10.1016/j.jbankfin.2018.10.010) define a stock-level dual-momentum strategy by first separating stocks on own-return sign and then applying cross-sectional sorts.
- [Ha and Fabozzi (2022)](https://doi.org/10.3905/jpm.2022.1.336) directly test a Dual Momentum strategy in a portfolio-allocation context.

### Scientific Skepticism and Replication Standards

- [Harvey, Liu and Zhu (2016)](https://doi.org/10.1093/rfs/hhv059) establish a higher evidentiary burden under multiple testing.
- [McLean and Pontiff (2016)](https://doi.org/10.1111/jofi.12365) document out-of-sample and post-publication decay across published return predictors.
- [Open Source Asset Pricing](https://www.openassetpricing.com/) provides reproducible infrastructure for cross-sectional predictors but does not establish Dual Momentum as an independent construct.
- Kim, Tse and Wald's [Time Series Momentum and Volatility Scaling](https://doi.org/10.1016/j.finmar.2016.05.003) shows that implementation layers such as volatility scaling can materially affect conclusions attributed to momentum rules.

## Existing Construct Relationship Assessment

| Existing construct | Relationship | RP-001 status |
| --- | --- | --- |
| CSM-001 | Direct relative-selection component | Established overlap |
| TSM-001 | Direct absolute/own-trend component | Established overlap |
| ISM-001 | Potential ranked universe or group-level implementation | Plausible but implementation-dependent |

CSM-001 is a completed cross-sectional relative-leadership construct. TSM-001 is a completed own-trend/risk-state construct. ISM-001 is a completed industry-level cross-sectional edge construct. Dual Momentum does not introduce a clearly separate input domain; it specifies how existing momentum information may be combined in a decision workflow.

## Incremental Information Assessment

The scientifically important unresolved question is whether combining relative and absolute momentum provides incremental information or complementary decision value beyond each component alone.

RP-001 does not answer that question. It only determines that this is better framed as a preregistered component-interaction or composite-workflow study using frozen CSM-001 and TSM-001 evidence, rather than as a new independent construct lifecycle.

## Data and Constructability Assessment

Public adjusted price or total-return data are sufficient in principle. Look-ahead-safe implementation is feasible using lagged observations and fixed decision dates.

However, direct Dual Momentum implementations require choices that materially define the workflow:

- Investment universe.
- Relative ranking method.
- Absolute comparison or reference series.
- Risk-free or defensive asset definition.
- Signal timing and rebalance frequency.
- Missing-data and asset-inception policy.
- Corporate-action and survivorship treatment.

These choices demonstrate high implementation feasibility but do not establish independent construct status.

## Supported By Evidence

- Dual Momentum is a recognized and practically relevant momentum-combination framework.
- Its two primary components have mature scientific foundations.
- Direct academic and practitioner studies exist.
- A deterministic, reproducible implementation is feasible after preregistration.
- Testing component complementarity has legitimate scientific value.

## Not Supported By Evidence

- Dual Momentum is an independent edge mechanism separate from CSM and TSM.
- The combined rule has a unique theoretical mechanism not inherited from its components.
- A new full construct lifecycle would add more information than a direct preregistered interaction study.
- Any claim of predictive power, profitability, alpha or production readiness.

## RP-001 Conclusion

DM-001 receives a **NO-GO** decision as an independent Edge Construct.

This decision does not reject Dual Momentum as a portfolio-research topic and does not claim that the combination lacks predictive or economic value. It concludes only that the current evidence supports treating Dual Momentum as a composite of already validated construct families, not as a scientifically independent construct.

The DM-001 lifecycle terminates at RP-001. LR-001 is not authorized.
