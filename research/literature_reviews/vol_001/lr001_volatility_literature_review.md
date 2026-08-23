# VOL-001 / LR-001: Market Volatility Literature Review

## Purpose

This review summarizes what the academic and practitioner literature says about **Market Volatility** as a financial construct.

It is descriptive only. It does not define the official VOL-001 construct, select a volatility estimator, test prediction, evaluate trading performance, or assess economic utility.

## 1. How Market Volatility Is Defined

Market volatility is generally defined as the magnitude of variation in asset prices or returns over a given horizon.

In finance literature, volatility is most often represented as variance or standard deviation of returns, realized variation, conditional variance, or option-implied expected variation. The common thread is dispersion, not direction.

Volatility is therefore distinct from:

- **Trend:** direction of price movement.
- **Momentum:** persistence of return direction or relative performance.
- **Liquidity:** cost, depth, immediacy, resiliency or price impact of trading.
- **Alpha:** expected excess return.

## 2. Main Volatility Dimensions

The literature supports several distinct volatility dimensions:

- **Historical realized volatility:** ex-post variation computed from observed returns.
- **High-frequency realized volatility:** realized variation from intraday return sampling.
- **Range-based volatility:** volatility estimated from high, low, open and close prices.
- **Conditional volatility:** time-varying variance modeled from past shocks and past variance.
- **Implied volatility:** market-implied expected future volatility extracted from option prices.
- **Cross-sectional volatility / dispersion:** variation across securities rather than through time.
- **Volatility persistence:** tendency of volatility levels to remain elevated or suppressed.
- **Volatility clustering:** empirical pattern where large changes tend to be followed by large changes and small changes by small changes.

## 3. Measurement Families

| Family | Typical Examples | Data Requirement | Main Dimension |
| --- | --- | --- | --- |
| Close-to-close realized | rolling standard deviation of log returns | daily close | historical realized variation |
| High-frequency realized | realized variance from intraday returns | intraday prices | high-frequency realized variation |
| Range-based | Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang | OHLC | intraperiod dispersion |
| ATR-derived | Average True Range, ATR percent | OHLC | range and gap magnitude |
| Conditional model-based | ARCH, GARCH and variants | returns | conditional expected variance |
| Implied volatility | VIX-style measures | option prices and rates | expected future volatility |
| Cross-sectional | dispersion of stock returns | panel returns | market breadth of variation |

No single volatility measure dominates all contexts. The appropriate measure depends on the research question, data availability, market structure and horizon.

## 4. Theoretical Foundations

The literature explains volatility-state behavior through several mechanisms:

- **Information arrival:** new information changes prices and increases return variation.
- **Volatility clustering:** volatility shocks persist over time.
- **Leverage and asymmetry:** negative market moves often coincide with larger future volatility changes than positive moves.
- **Risk compensation:** volatility is treated as a core risk variable in portfolio theory and derivatives.
- **Market stress:** uncertainty, deleveraging, liquidity pressure and risk-off behavior can elevate volatility.
- **Option-market expectations:** option prices embed expectations and risk premia regarding future volatility.

## 5. Empirical Findings Reported in Literature

The literature strongly supports volatility as observable, persistent and time-varying.

Representative findings include:

- Returns often show weak autocorrelation, while absolute or squared returns show stronger persistence.
- ARCH/GARCH models were developed specifically to model time-varying conditional variance.
- Realized volatility provides a nonparametric ex-post measure of return variation and is central to volatility forecasting literature.
- Range-based estimators can use more intraday information than close-to-close returns when OHLC data is available.
- Implied volatility measures such as VIX represent option-market expectations of near-term volatility.
- Volatility measurement is sensitive to sampling frequency, jumps, overnight gaps, microstructure noise, estimator assumptions and horizon.

## 6. Literature Maturity

Market Volatility has very high literature maturity.

It is central to:

- financial econometrics
- portfolio risk management
- option pricing
- volatility forecasting
- derivatives markets
- risk budgeting
- volatility targeting
- stress monitoring

## 7. Limitations in the Literature

The main limitation is measurement plurality.

Volatility can mean realized past variation, expected future variation, model-implied conditional variance, intraday range variation or cross-sectional dispersion.

Additional limitations include:

- Close-to-close measures ignore intraday path information.
- Range-based estimators rely on assumptions about price processes and market hours.
- High-frequency realized volatility can suffer from market microstructure noise.
- Implied volatility includes both expected volatility and volatility risk premia.
- GARCH-style models require parametric assumptions and estimation choices.
- ATR measures are interpretable but not the same as variance estimators.
- Cross-sectional volatility measures a different construct than time-series volatility.

## 8. Open Research Gaps

For VOL-001, the key unresolved question is not whether volatility exists as a construct. It does.

The open question is:

```text
Which precise volatility dimension should become the frozen VOL-001 scientific sensor?
```

Candidate directions for CD-001 include:

- realized time-series volatility
- OHLC range-based volatility
- implied volatility
- ATR-derived volatility state
- cross-sectional volatility state

Each would represent a different scientific construct.

## LR-001 Conclusion

Market Volatility is strongly supported by the literature as a fundamental financial construct.

It is mature, measurable, theoretically grounded and distinct from direction, alpha, liquidity and regime.

The literature supports moving VOL-001 to `CD-001`, where one narrow operational definition must be selected and frozen.

## Authorized Next Stage

`VOL-001 / CD-001`

