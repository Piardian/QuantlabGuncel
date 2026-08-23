# LIQ-001 / LR-001: Market Liquidity Literature Review

## Purpose

This review summarizes what the academic and professional literature says about Market Liquidity as a financial construct.

It is descriptive only. It does not define the official LIQ-001 construct, select variables, test prediction, evaluate profitability, or assess economic utility.

## 1. How Market Liquidity Is Defined

Market Liquidity is generally defined as the ability to transact quickly, in meaningful size, at low cost, and with limited price impact.

The literature treats liquidity as multidimensional rather than as a single scalar property. A liquid market is typically one where trading is inexpensive, execution is available quickly, sufficient size exists near current prices, and prices recover after order-flow shocks.

## 2. Main Liquidity Dimensions

The dominant dimensions are:

- **Tightness:** cost of immediate trading, often represented by bid-ask spread or effective spread.
- **Depth:** quantity available near current prices.
- **Immediacy:** speed with which trades can be completed.
- **Breadth:** availability of liquidity across price levels or trade sizes.
- **Resiliency:** speed of recovery after liquidity shocks.
- **Price impact:** price movement caused by trade size or order flow.

The IMF liquidity measurement framework explicitly organizes measures around tightness, immediacy, depth, breadth, and resiliency. Kyle's market microstructure work emphasizes tightness, depth, and resiliency.

## 3. Measurement Families

The literature supports several measurement families:

| Family | Typical Examples | Data Requirement | Main Dimension |
| --- | --- | --- | --- |
| Spread-based | quoted spread, effective spread, Roll spread | quotes or prices | tightness |
| Volume/turnover-based | share turnover, dollar volume | daily OHLCV | trading activity / capacity |
| Price-impact | Kyle lambda, Amihud illiquidity, Hasbrouck impact | daily or intraday trades | impact / depth |
| Zero-return / transaction-cost proxy | Lesmond-Ogden-Trzcinka | daily returns | implicit trading friction |
| Order-book | quoted depth, order book imbalance | high-frequency book data | depth / immediacy |
| Resiliency | recovery of spreads/depth after shocks | intraday or event data | resiliency |
| Aggregate liquidity | market-wide spread, depth, or reversal measures | panel data | systematic liquidity state |

No single measure dominates across all research contexts.

## 4. Theoretical Foundations

Liquidity is explained through several mechanisms:

- Transaction costs: trading requires compensation through spreads or price concessions.
- Inventory risk: market makers require compensation for holding risky inventory.
- Asymmetric information: informed trading increases adverse selection and widens spreads.
- Funding constraints: trader balance-sheet constraints reduce liquidity provision.
- Market stress: liquidity can deteriorate when volatility, uncertainty, or funding pressure rises.
- Commonality: liquidity can move together across assets, creating systematic liquidity conditions.

## 5. Empirical Findings

The literature broadly supports liquidity as an observable market construct.

Representative findings include:

- Liquidity has multiple dimensions and must often be measured with multiple proxies.
- Illiquidity and expected returns are related in some cross-sectional and time-series studies.
- Market-wide liquidity risk has been studied as a priced state variable.
- Liquidity conditions can co-move across securities and markets.
- Funding liquidity and market liquidity can reinforce each other during stress episodes.
- Liquidity measurement is sensitive to asset class, market structure, data frequency, and sample period.

## 6. Literature Maturity

Market Liquidity has high literature maturity.

It is central to:

- market microstructure
- transaction-cost analysis
- execution research
- asset pricing
- financial stability
- portfolio capacity
- stress monitoring

## 7. Limitations in the Literature

The main limitation is dimensionality.

Liquidity can mean spread, depth, impact, immediacy, turnover, resiliency, or systematic liquidity risk depending on context. This creates measurement ambiguity.

Daily data can support some proxies such as Amihud illiquidity, dollar volume, turnover, and Roll-style spread estimates, but direct depth, immediacy, and resiliency often require quote, trade, or order-book data.

## 8. Open Research Gaps

Key gaps include:

- whether daily proxies are sufficient for broad equity research
- how to separate liquidity from volatility and regime stress
- which liquidity dimension is most relevant for prediction versus execution versus capacity
- whether market-wide liquidity states add information beyond market-regime constructs
- whether liquidity constructs remain stable across decades and market structures

## LR-001 Conclusion

Market Liquidity is strongly supported by the literature as a fundamental financial construct.

It is multidimensional, distinct from volatility and market regime, and mature enough to justify a formal CD-001 construct definition stage.

## Authorized Next Stage

`LIQ-001 / CD-001`

