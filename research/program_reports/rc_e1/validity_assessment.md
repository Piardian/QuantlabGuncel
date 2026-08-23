# RC-E1 Validity Assessment

## Internal Consistency

The completed studies are internally consistent within their stated scopes.

- RC-A found no measurable EMA filter contribution or economically meaningful interaction.
- RC-B found no supported ATR contribution, no economically meaningful ATR-Breakout interaction, and no support for positive contribution from the current Breakout Confirmation implementation.
- RC-C found no stable, practically meaningful entry-feature association in the production-selected trade population.
- RC-D reproduced two weak EMA-distance associations but classified overall reproducibility as inconclusive.

The RC-D EMA-distance result is not a conflict with RC-A. RC-A evaluated interventional filter removal, while RC-C/D evaluated a continuous entry feature within an already selected trade population. Neither study type estimates the same quantity.

## Threats To Validity

| Threat | Relevance to current evidence |
| --- | --- |
| Historical data scope | Findings apply only to the evaluated historical windows, daily frequency, and Yahoo Finance data. |
| Survivorship bias | The broad universe uses current S&P 500 constituents and is not survivorship-free. |
| Portfolio simulation | Main research runs are independent single-symbol accounts, not a shared-capital portfolio simulation. |
| Execution assumptions | Results depend on modeled commission, slippage, fills, and deterministic Backtrader behavior. |
| Commission and slippage | Fixed assumptions may differ from actual market impact, spreads, borrow, liquidity, and execution latency. |
| Deterministic variants | Sign-flip statistics are descriptive uncertainty measures, not randomized causal p-values. |
| Selection bias | RC-C conditions on trades already accepted by the production selection pipeline. |
| OOS coverage | RC-D has 1,160 trades in one partial 2026 year; symbol-level reproducibility was not evaluable at the RC-C1 minimum sample threshold. |
| Multiple testing | Multiple component and association questions increase chance-finding risk. |
| Paper and live absence | No paper-trading or live-execution evidence is available. |

## Validity Judgment

The evidence is sufficient to state what the completed experiments did not support within the stated backtest scope. It is insufficient for causal, universal, portfolio-level, paper-trading, or live-trading validity claims.
