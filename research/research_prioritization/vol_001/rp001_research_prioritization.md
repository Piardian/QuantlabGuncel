# VOL-001 / RP-001: Research Prioritization

## Purpose

Determine whether **Market Volatility State** should become a standalone construct in the Market Signal Discovery Program v3.0.

This stage evaluates research priority only. It does not define the final construct, choose a volatility estimator, run empirical tests, evaluate prediction, or assess economic utility.

## Primary Decision

**GO**

VOL-001 should proceed to `VOL-001 / LR-001`.

## Evidence Summary

Market volatility is one of the most established constructs in empirical finance, financial econometrics, derivatives, portfolio risk management and market microstructure.

The literature supports multiple volatility measurement families, including close-to-close realized volatility, high-frequency realized volatility, range-based OHLC estimators, ARCH/GARCH-style conditional volatility models, stochastic volatility models and option-implied volatility indices.

VOL-001 is scientifically distinct from MR-001 and LIQ-001:

- MR-001 models latent market regime using SPY returns and realized volatility.
- LIQ-001 measures aggregate price-impact liquidity stress.
- VOL-001 would directly measure the current volatility state itself.

This distinction matters because volatility is not merely a byproduct of directional trend or liquidity stress. It is a core market state variable used for risk measurement, derivative pricing, volatility forecasting, portfolio allocation and drawdown-aware decision support.

## Evaluation Dimensions

| Dimension | Assessment | Rationale |
| --- | --- | --- |
| Scientific relevance | High | Volatility is a foundational construct in modern finance, econometrics, option pricing and risk management. |
| Theoretical foundation | High | The literature documents volatility clustering, time-varying risk, volatility persistence and volatility state changes. |
| Construct independence | High | Volatility overlaps with regime and liquidity but is conceptually distinct from direction, return, alpha and transaction friction. |
| Literature maturity | High | Foundational work includes ARCH/GARCH, realized volatility, range-based estimators and implied volatility research. |
| Data availability | High | Daily OHLCV data supports multiple reproducible estimators; implied volatility is available through VIX-like sources if selected later. |
| Measurability | High | Multiple mathematically precise volatility estimators exist. |
| Practical importance | High | Volatility directly affects risk sizing, drawdown risk, option pricing, hedging, exposure control and capital allocation. |
| Expected research contribution | High | VOL-001 can clarify volatility state independently from MR-001 and LIQ-001 and may become a scientific sensor for risk-aware decisions. |

## Candidate Measurement Families for LR-001

The next stage should review at least:

- Historical close-to-close realized volatility
- High-frequency realized volatility
- Parkinson range-based volatility
- Garman-Klass range-based volatility
- Rogers-Satchell range-based volatility
- Yang-Zhang volatility
- ATR-derived volatility
- ARCH/GARCH conditional volatility
- Stochastic volatility
- Implied volatility such as VIX
- Cross-sectional volatility and dispersion

This list is not a final construct definition. It is a literature-review scope.

## Supported Claims at RP Stage

- Market volatility is a recognized financial construct.
- Volatility has mature academic and practitioner literature.
- Volatility is distinct from directional movement and alpha.
- Volatility can be operationalized reproducibly.
- A dedicated VOL-001 research program is scientifically justified.

## Not Supported at RP Stage

- Any specific volatility estimator is superior.
- VOL-001 predicts returns.
- VOL-001 improves trading performance.
- VOL-001 has economic value in this project.
- VOL-001 should modify any production strategy.

## Decision

VOL-001 receives a **GO** decision for the next stage.

The next authorized stage is:

`VOL-001 / LR-001: Market Volatility Literature Review`

