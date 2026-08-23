# HG-002 Mechanism Hypotheses

## Scope

This is hypothesis generation, not empirical validation. The production implementation named `Leadership Quality` does not measure corporate, sector, capitalization, or cross-sectional leadership. It operationalizes **multi-horizon relative-strength persistence versus SPY**:

```text
Precondition: RS60 > 5% and StockReturn60 > SPYReturn60
Persistence condition: RS20 > 0 OR RS120 > 10%
RSx = StockReturnx - SPYReturnx
```

The mechanisms below are a practical, non-exhaustive catalogue of scientifically plausible explanations. Their theoretical-support classifications refer to literature plausibility only; they are not evidence for this strategy.

## M1: Cross-Sectional Momentum Continuation

**Theoretical support:** Strong.

**Rationale:** Historical winner-minus-loser return continuation is a central momentum finding. A stock that has outperformed SPY over several horizons could be a persistence candidate, rather than a leader in a corporate or sector sense.

**Why the filter could capture it:** RS60 selects medium-horizon relative outperformance; RS20 and RS120 seek either current persistence or durable longer-horizon relative performance.

**Predictions if true:** Greater persistent RS should accompany more favorable post-entry continuation, more favorable R outcomes, and fewer early failures in a suitable population.

**Weakening observations:** No robust association across separated periods, no OOS repetition, or disappearance after addressing relevant confounding and selection design.

**Open question:** Does multi-horizon RS associate with post-entry continuation in candidate signals, not only trades already selected by production filters?

## M2: Gradual Information Diffusion

**Theoretical support:** Moderate.

**Rationale:** Information can diffuse gradually across heterogeneous investors, allowing price underreaction before broader incorporation.

**Why the filter could capture it:** Return persistence across 20, 60, and 120 days may be a coarse price-only trace of information being incorporated over time.

**Predictions if true:** The association should be stronger near information-rich events, show intermediate-horizon continuation, and eventually weaken or reverse at sufficiently long horizons.

**Weakening observations:** No event-time pattern, no relation to independently identified information events, or no difference from matched controls.

**Open question:** Does relative-strength persistence vary with earnings-news or other information-event timing?

## M3: Institutional Demand and Slow-Moving Capital

**Theoretical support:** Moderate.

**Rationale:** Persistent allocation by large investors or constrained arbitrage capital could create sustained relative demand.

**Why the filter could capture it:** Sustained price strength may proxy persistent demand, but the implementation contains no ownership, flow, or order-flow variable.

**Predictions if true:** Persistent RS should coincide with independent demand proxies, durable trends, and fewer abrupt reversals.

**Weakening observations:** No relationship to observed institutional flows, ownership changes, or other independent demand measures.

**Open question:** Do institutional-flow or ownership measures explain the same patterns as multi-horizon RS?

## M4: Behavioral Extrapolation and Herding

**Theoretical support:** Moderate.

**Rationale:** Investors may extrapolate strings of favorable outcomes or herd into perceived winners, producing continuation at some horizons and possible later reversal.

**Why the filter could capture it:** RS20/60/120 detects a sequence of benchmark-relative returns that could be subject to extrapolation.

**Predictions if true:** Intermediate-horizon continuation should coexist with horizon-dependent exhaustion or reversal, and associations may vary with sentiment or attention proxies.

**Weakening observations:** No distinct continuation/reversal horizon structure and no relation to independent sentiment or attention proxies.

**Open question:** Does persistent RS show different continuation and reversal behavior across horizons and market states?

## M5: Risk Compensation or Latent Factor Exposure

**Theoretical support:** Moderate.

**Rationale:** Relative outperformance may reflect compensation for unmeasured systematic, sector, growth, volatility, or crash-risk exposure rather than mispricing or behavioral continuation.

**Why the filter could capture it:** The filter compares only with SPY and does not neutralize sector or factor exposure.

**Predictions if true:** RS groups should differ in independent factor exposures, and apparent associations may weaken after appropriate matching or adjustment.

**Weakening observations:** No meaningful exposure difference or a robust relationship after an appropriate risk design.

**Open question:** Does multi-horizon RS retain an association after matching on sector, beta, volatility, and factor exposures?

## M6: Benchmark-Relative Demand Persistence

**Theoretical support:** Weak.

**Rationale:** The operationalization may measure allocation pressure relative to SPY, not broad leadership.

**Why the filter could capture it:** Every RS quantity is defined against SPY; the result can therefore depend on benchmark construction.

**Predictions if true:** Findings should change when SPY is replaced by a sector, style, or industry benchmark.

**Weakening observations:** Equivalent results against unrelated benchmarks or no relationship to benchmark-relative allocation measures.

**Open question:** Is the pattern specific to SPY comparison, or does it persist against sector and style benchmarks?

## M7: Market Microstructure and Liquidity Transmission

**Theoretical support:** Speculative.

**Rationale:** Relative price strength can coincide with liquidity, spread, turnover, or order-imbalance conditions even if it does not directly measure them.

**Why the filter could capture it:** It does not directly capture them; any relationship is indirect and currently unmeasured.

**Predictions if true:** RS persistence should vary across liquidity tiers and co-move with independent liquidity or order-flow measures.

**Weakening observations:** No relation to such measures when they are independently observed.

**Open question:** Are RS persistence and post-entry behavior different across liquidity and trading-cost strata?

## Literature Context

- Jegadeesh and Titman (1993) document medium-horizon winner-minus-loser continuation; this supports momentum plausibility, not this strategy. [Journal of Finance record](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)
- Hong and Stein (1999) provide a model of gradual information diffusion, momentum, and later overreaction. [Harvard publication record](https://stein.scholars.harvard.edu/publications/unified-theory-underreaction-momentum-trading-and-overreaction-asset-markets)
- Barberis, Shleifer, and Vishny (1998) provide a behavioral sentiment model with underreaction and overreaction. [Harvard archive](https://dash.harvard.edu/entities/publication/73120378-fd05-6bd4-e053-0100007fdf3b)
