# LR-001 Momentum and Relative Strength Literature Review

## Review Protocol

This is a structured narrative review, not a formal statistical meta-analysis. Sources were prioritized as follows: broad reviews, seminal peer-reviewed papers, international evidence, replication/qualification evidence, then practitioner methodology. Practitioner material is explicitly separated from academic evidence.

## 1. Momentum Definitions

### Cross-Sectional Momentum

The canonical equity definition ranks a fixed universe by past return, buys relative winners, and sells relative losers. Formation and holding horizons commonly span 3-12 months. A widely used implementation is 12-1: trailing 12-month return while omitting the most recent month. Jegadeesh and Titman (1993) documented winner-minus-loser continuation over 3-12 month horizons in U.S. equities. [Source](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)

### Time-Series Momentum

Time-series momentum conditions on an asset's own past return sign, rather than its rank relative to peers. Moskowitz, Ooi, and Pedersen (2012) reported 1-12 month return persistence across a diversified set of futures contracts, with partial longer-horizon reversal. [Source](https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf)

### Other Families

Residual, industry, 52-week-high, risk-managed, and factor momentum variants are active research areas. A 30-year review distinguishes cross-sectional and time-series constructions and surveys alternative methods; a systematic/bibliometric review identifies several momentum research clusters. [30-year review](https://link.springer.com/article/10.1007/s11408-022-00417-8) [systematic review](https://ideas.repec.org/a/spr/manrev/v72y2022i1d10.1007_s11301-020-00205-6.html)

See `momentum_definitions.csv` for compact definitions.

## 2. Relative Strength Definitions

Academic relative strength is usually a cross-sectional rank or portfolio-sort concept, not merely a return minus one benchmark. Common operationalizations include top-decile prior-return portfolios, industry-relative return, benchmark-relative return, percentile scores, and volatility-adjusted composite scores.

See `relative_strength_definitions.csv`.

## 3. Strongest Empirical Support

The deepest evidence base is medium-horizon cross-sectional momentum in equities and diversified time-series momentum in futures. International evidence is substantial: Rouwenhorst (1998) reported medium-term continuation across 12 countries, while Fama and French (2012) reported return momentum in their sampled regions except Japan. [Rouwenhorst](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.95722) [Fama-French](https://ideas.repec.org/a/eee/jfinec/v105y2012i3p457-472.html?viewClass=Print&viewType=Print)

Asness, Moskowitz, and Pedersen (2013) reported momentum premia across diverse markets and asset classes, while also emphasizing that common risk and liquidity considerations remain relevant. [Source](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12021)

## 4. Inconsistent Evidence and Qualifications

There is no single universally dominant lookback, benchmark, ranking, weighting, or rebalance convention. International results vary by region and size; Fama and French's sample is a notable qualification for Japan. Evidence is also conditional on implementation details and market state.

Momentum can experience severe episodic losses. Daniel and Moskowitz (2016) identify momentum crashes in panic-like states following market declines, high volatility, and rebounds. [Source](https://www.researchgate.net/publication/307997631_Momentum_crashes)

## 5. Robustness Across Markets and Regimes

- **U.S. equities:** canonical cross-sectional evidence is strong historically, but realized results depend on construction and costs.
- **International equities:** substantial evidence exists, with country and size qualifications.
- **Different decades:** long literature supports persistence, but magnitudes are time-varying and post-publication performance, crowding, and implementation deserve separate scrutiny.
- **Bull/bear and volatility states:** momentum is not regime-invariant; crash risk and rebound sensitivity are important qualifications.
- **High/low volatility:** volatility scaling and risk management are widely studied, but do not prove a universal improvement for every implementation.

## 6. Main Theoretical Explanations

Competing explanations include gradual information diffusion, behavioral underreaction and extrapolation, institutional demand or slow-moving capital, and rational risk or liquidity exposure. Hong and Stein's model provides a gradual-diffusion account of underreaction, momentum trading, and longer-horizon overreaction. Barberis, Shleifer, and Vishny provide a behavioral sentiment model that can generate under- and overreaction. [Hong-Stein](https://stein.scholars.harvard.edu/publications/unified-theory-underreaction-momentum-trading-and-overreaction-asset-markets) [Barberis-Shleifer-Vishny](https://dash.harvard.edu/entities/publication/73120378-fd05-6bd4-e053-0100007fdf3b)

No single explanation has decisive consensus across all markets and momentum definitions.

## 7. Criticisms

- Data mining and multiple-testing risk are material for proliferating factor variants.
- High turnover, transaction costs, liquidity, capacity, and market impact can reduce implementable returns.
- Momentum may be crowded and can suffer sharp crash episodes.
- Regime dependence complicates unconditional average-return interpretation.
- Survivorship, delisting treatment, universe construction, and benchmark choice can materially affect results.
- Academic portfolio results and practitioner products are not interchangeable.

## 8. Production Implementation Comparison

See `comparison_with_production.md`. The production gate resembles benchmark-relative multi-horizon persistence but is not a canonical academic cross-sectional ranking methodology.

## 9. Practitioner Research: Separate Evidence Category

Official MSCI methodology combines risk-adjusted 6- and 12-month momentum scores, parent-index selection, weighting, caps, buffers, and rebalancing rules. This shows a common practitioner operationalization, not independent proof that any specific implementation is effective. [MSCI methodology](https://www.msci.com/indexes/documents/methodology/2_MSCI_Momentum_Indexes_Methodology_20250725.pdf)

## Conclusion

The literature supports momentum as a broad research family with meaningful historical evidence in specific constructions and markets. It also supports substantial qualifications around definition, regime, costs, and implementation. It does not validate the current production rule.
