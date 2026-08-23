# LR-001: Market Regime Literature Review

## Scope

This review summarizes the academic and practitioner literature on market regime as a financial construct.
It is descriptive only. It does not test trading performance or predictive validity.

## 1. How Market Regime is Defined

The literature uses "market regime" to mean a latent or observable state in which the return-generating process changes in a persistent way. The most common definitions are:

- Bull vs bear market states, usually based on sustained positive or negative market performance.
- High-volatility vs low-volatility states.
- Risk-on vs risk-off states.
- Hidden-state regimes inferred from statistical models such as Markov-switching or HMMs.

This framing is strongly supported by the regime-switching literature and survey work in financial economics. Hamilton's regime-switching framework is the canonical starting point, and later reviews by Ang & Timmermann summarize how the concept generalizes across returns, volatility, correlations, and macro variables. [Hamilton 1989](https://www.ssc.wisc.edu/~bhansen/718/Hamilton1989.pdf), [Ang & Timmermann 2012](https://ideas.repec.org/a/anr/refeco/v4y2012p313-337.html), [Hamilton regime-switching review](https://econweb.ucsd.edu/~jhamilto/palgrav1.pdf)

## 2. Theoretical Mechanisms

The literature usually explains regime shifts as arising from time-variation in:

- Expected returns
- Volatility
- Correlations and covariance structure
- Macro conditions and policy states
- Investor learning or gradual information diffusion

The strongest support is for latent state-switching in returns and volatility, with macroeconomic and financial stress variables often used to interpret the states after estimation. [Ang & Timmermann 2012](https://ideas.repec.org/a/anr/refeco/v4y2012p313-337.html), [Guidolin & Timmermann](https://files.stlouisfed.org/files/htdocs/wp/2005/2005-002.pdf), [ECB financial stress regimes](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2057.en.pdf)

## 3. Common Taxonomies

The most common taxonomies are:

- Bull / bear
- Expansion / contraction
- Risk-on / risk-off
- High volatility / low volatility
- Multi-state hidden regimes

Bull/bear taxonomies are usually the most interpretable for practitioners, while hidden regimes are the most common in academic estimation work. The literature also notes that there is no single agreed definition of bull or bear state. [Top-down bull/bear states](https://pureadmin.qub.ac.uk/ws/files/137453711/Bullbear_TD_IRFA_Revised.pdf), [Market regime classification using correlation networks](https://econ.unc.edu/wp-content/uploads/sites/1423/2019-Mayo-Zhu_Nam.pdf)

## 4. Observable Variables Used

Common observables include:

- Price returns and cumulative drawdowns
- Volatility and realized volatility
- Correlations / covariance matrices
- Breadth and industry participation
- Liquidity and credit stress proxies
- Macro variables such as sentiment, debt service, inflation, and business-cycle indicators

This is strongly supported in the literature. Different papers emphasize different observables, but return/volatility and cross-asset correlation are the most common starting points. [Ang & Timmermann 2012](https://ideas.repec.org/a/anr/refeco/v4y2012p313-337.html), [Market regime classification using correlation networks](https://econ.unc.edu/wp-content/uploads/sites/1423/2019-Mayo-Zhu_Nam.pdf), [How to predict financial stress?](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2057.en.pdf)

## 5. Methodologies Used

The most frequently used methodologies are:

- Markov-switching / hidden Markov models
- Threshold autoregressive models
- State-space models
- Bayesian regime-switching models
- Clustering and unsupervised classification
- Rule-based ex post classification

Markov-switching models are the dominant academic framework, but practitioner work often uses simpler state rules or hybrid ML classifiers. [Hamilton 1989](https://www.ssc.wisc.edu/~bhansen/718/Hamilton1989.pdf), [Regime-switching models review](https://www.mdpi.com/2227-7390/13/7/1128), [Market regime detection using HMMs](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/)

## 6. Empirical Findings

The literature broadly agrees that regime-dependent behavior exists in financial markets. Regime-switching models often fit returns and volatility better than a single linear model, and regime-conditional asset allocation can improve diversification or risk control in some studies. Evidence is also commonly reported for distinct bull and bear phases in equity markets. [Regime Changes and Financial Markets](https://rady.ucsd.edu/_files/faculty-research/timmermann/regime_changes_June_22.pdf), [Asset allocation under multivariate regime switching](https://files.stlouisfed.org/files/htdocs/wp/2005/2005-002.pdf), [Predictability of Bull and Bear Markets](https://www.uni-trier.de/fileadmin/fb4/prof/VWL/EWF/Research_Papers/2020-01.pdf)

However, the literature is less unified on precise regime boundaries, transition timing, and whether any particular observable regime taxonomy is stable across assets, decades, and frequency.

## 7. Limitations Reported in the Literature

Commonly reported limitations include:

- No single agreed definition of regime
- Identification lag when regimes are inferred ex post
- Parameter instability across samples
- Sensitivity to sample period and asset class
- Classification error near turning points
- Model risk when regimes are too granular
- Regime labeling often depends on the chosen observable set

These limitations are repeatedly emphasized in survey and methodological papers. [Ang & Timmermann 2012](https://ideas.repec.org/a/anr/refeco/v4y2012p313-337.html), [Top-down bull/bear states](https://pureadmin.qub.ac.uk/ws/files/137453711/Bullbear_TD_IRFA_Revised.pdf), [On Regime Switching Models](https://www.mdpi.com/2227-7390/13/7/1128)

## 8. Open Research Gaps

Open questions remain around:

- Robust regime definitions that transfer across markets and decades
- Real-time detection versus ex post classification
- How much information regimes add beyond standard trend and volatility features
- Whether regime labels are stable at different horizons
- Whether regime models generalize outside the asset classes they were fit on

## Bottom Line

The literature strongly supports the idea that markets exhibit regime-like behavior. It also strongly supports using returns, volatility, correlation structure, and macro stress variables to identify those states. What remains unresolved is a universal regime taxonomy and a single best operational definition.

