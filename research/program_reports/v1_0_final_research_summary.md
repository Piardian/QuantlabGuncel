# v1.0 Final Research Summary

## Purpose

Evaluate whether the examined production components of `leadership_expansion_v1` show measurable, consistent information contribution under the current historical data, universe, backtest engine, and execution assumptions.

The program covered filter necessity, filter interaction, observational entry-feature associations, and out-of-sample reproducibility. It does not establish causality, universal validity, or live tradability.

## Research Taxonomy

| Family | Method | Primary question | Cannot conclude |
| --- | --- | --- | --- |
| RC-A | Interventional | Does a filter show independent contribution? | Why an observed effect occurs internally |
| RC-B | Interventional | Do two filters show an interaction contribution? | Trade-lifecycle behavior |
| RC-C | Observational | Which entry features associate with outcomes within selected trades? | That a feature creates edge or contributes independently |
| RC-D | Predictive / OOS | Do RC-C associations reproduce on disjoint data? | Causal contribution |

Association is not contribution, and contribution is not causation. An integrated assessment must retain those boundaries.

## RC-A: EMA Trend Research Program

**Question:** Do EMA200 Price and EMA200 Slope filters show independent or joint contribution?

**Evidence:**

- Removing either filter independently left the 21,655 baseline trade records and pooled quality metrics unchanged.
- Removing both added 560 net trades, but Avg R changed by only `-0.00106R`.
- The Avg R interaction bootstrap interval crossed zero and the effect was economically negligible under the preregistered `0.02R` threshold.

**Conclusion:** Independent contribution, information interaction, and economic contribution were not supported in the current architecture.

**Status:** Closed (current evidence).

## RC-B: ATR Expansion and Breakout Research Program

**Question:** Do ATR Expansion and Breakout Confirmation show independent or interaction contribution?

**Evidence:**

- ATR Expansion removal changed Avg R by `+0.01169R`; its bootstrap interval crossed zero. Classification: `None`.
- Breakout Confirmation removal changed Avg R by `+0.02112R`; its bootstrap interval was positive. The direction did not support a positive contribution from the current breakout filter. Classification: `Weak`.
- The combined-removal Avg R interaction was `+0.01095R`; its bootstrap interval crossed zero and the magnitude was below `0.02R`. Classification: `None`.

**Conclusion:** ATR independent contribution was not supported. Positive independent contribution from the current Breakout Confirmation implementation was not supported. No economically meaningful interaction was supported.

**Status:** Closed (current evidence).

## RC-C: Core Signal Attribution Audit

**Question:** Within executed production-selected trades, which entry features are associated with realized outcomes?

**Methodological scope:** Observational only. The study population had already passed the production selection pipeline. Results do not estimate independent contribution, edge creation, or causation.

**Evidence:**

- No positive entry-feature association of meaningful magnitude was observed.
- EMA50 and EMA200 distance showed weak negative pooled associations with R, and both were unstable across years and symbols.
- RS20, RS60, RS120, ATR expansion magnitude, and breakout strength did not show meaningful, stable associations.
- Leadership Quality was constant in the selected trade population, so its association was not measurable.
- Lifecycle variables separated outcomes: winners averaged 20.0 holding days versus 7.3 for non-winners; `TIME_EXIT` trades averaged `+3.61R`, `ATR_TRAIL` trades `+0.48R`, and `STOP` trades `-1.08R`.

**Conclusion:** Stable and practically meaningful entry-feature associations were not observed. Lifecycle variables describe performance realization after entry and are not interpreted as entry edge.

**Status:** Closed (observational evidence only).

## RC-D: Out-of-Sample Reproducibility Audit

**Question:** Do RC-C1 observational associations reproduce on disjoint, unseen production data?

**OOS population:** 1,160 executed trades across 356 symbols, with entries from 2026-01-05 through 2026-07-17. The population had no overlap with RC-C1 entries, whose final entry date was 2025-12-23.

**Evidence:**

- The weak negative associations for EMA200 and EMA50 distance reproduced with the same `Weak` magnitude class.
- The remaining entry features were inconclusive because their RC-C1 associations were negligible, lacked variation, or did not form a comparable association.
- The OOS dataset covered only one partial calendar year.
- No symbol reached the RC-C1 minimum of 20 OOS trades, so symbol-level reproducibility was not evaluable.

**Conclusion:** Overall reproducibility is `Inconclusive`. The two reproduced weak associations do not establish causality or general validity.

**Status:** Closed (limited OOS evidence).

## Program-Level Findings

### Interventional evidence

- EMA200 Price and EMA200 Slope contribution was not supported.
- ATR Expansion contribution was not supported.
- Positive contribution from the current Breakout Confirmation implementation was not supported.
- No strong, economically meaningful interaction evidence was found.

### Observational evidence

- No stable, practically meaningful entry-feature association with trade outcome was observed in the selected production trade population.
- Trade lifecycle variables visibly separated favorable and unfavorable realized outcomes, but do not explain entry edge.

### OOS evidence

- Strong reproduction of program findings was not demonstrated.
- The overall OOS reproducibility classification is `Inconclusive` because coverage is short and symbol-level repetition is unavailable.

## Methodological Limits

- The historical universe is based on current S&P 500 constituents and is not survivorship-free.
- Runs are independent single-symbol backtests, not a shared-capital portfolio simulation.
- Results depend on the current backtest engine, commission, slippage, data source, and deterministic execution assumptions.
- Multiple research questions increase the risk of chance findings.
- No paper-trading or live-execution validation has been performed.
- Findings should be read as evidence that supports or does not support a hypothesis within this scope, not as universal or causal claims.

## Overall Conclusion

Within the current research scope, the evidence does not support the hypothesis that the examined production entry filters in `leadership_expansion_v1` provide measurable and consistent information contribution. No stable, practically meaningful entry-feature association was observed, and OOS reproducibility remains inconclusive.

This conclusion applies only to the evaluated datasets, production architecture, universe, backtest assumptions, and research methods.

## Next Phase

RC-E, if opened, should be an **Evidence Synthesis and Validity Assessment** phase. It should evaluate the complete A-D evidence set and its limitations without introducing new strategy modifications, filter tests, or optimization.
