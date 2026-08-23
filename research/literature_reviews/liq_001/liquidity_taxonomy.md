# Liquidity Taxonomy

## Core Taxonomy

| Dimension | Meaning | Common Measures | Data Need |
| --- | --- | --- | --- |
| Tightness | Cost of immediate transaction | quoted spread, effective spread, Roll spread | quotes or prices |
| Depth | Quantity available near current price | order book depth, volume at best bid/ask | order book |
| Immediacy | Speed of execution without large cost | fill speed, executable size | trade/order data |
| Breadth | Ability to trade across sizes/levels | depth across order book levels | order book |
| Resiliency | Recovery after liquidity shock | spread/depth recovery time | intraday or event data |
| Price Impact | Price change caused by trading | Kyle lambda, Amihud, Hasbrouck impact | daily or intraday data |
| Trading Activity | Observed participation | volume, dollar volume, turnover | daily OHLCV |
| Systematic Liquidity | Market-wide liquidity state | aggregate liquidity factor, commonality | panel data |

## Primary Literature Consensus

The literature agrees that liquidity is not one-dimensional.

The most common framing is that a liquid market has low trading cost, sufficient depth, quick execution, and resilience after shocks.

## Taxonomy Boundary

This taxonomy does not select LIQ-001 variables. It maps the available literature for CD-001.

