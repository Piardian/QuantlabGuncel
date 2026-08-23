# EXB-002 Backtest Report

EXB-002 executed the frozen CSM-001 x TSM-001 workflow under the EXB-001 non-formal exploratory constraints.

No alpha logic was changed. No parameter optimization was performed. No broker mutation calls were made.

## Evidence Boundary

SURVIVORSHIP_INTEGRITY = PARTIAL  
PIT_INTEGRITY = PARTIAL  
CORPORATE_ACTION_LIMITATION = OPEN  
EVIDENCE = NON_FORMAL_EXPLORATORY_EVIDENCE

## Final Summary

```text
Program:
EXB-002 Non-Formal Exploratory Backtest

Evidence classification:
NON_FORMAL_EXPLORATORY_EVIDENCE

Universe:
EXB001_ALPACA_IEX_DAILY_REDUCED

Usable securities:
100

Backtest start:
2022-01-04

First valid signal:
2022-01-03

Backtest end:
2026-08-11

Number of rebalance events:
56

MAIN STRATEGY:
CSM-001 x TSM-001

Gross total return:
-12.90%

Gross CAGR:
-2.96%

Gross volatility:
33.76%

Gross Sharpe:
0.078

Gross maximum drawdown:
-59.53%

Net total return:
-13.49%

Net CAGR:
-3.10%

Net volatility:
33.76%

Net Sharpe:
0.074

Net Sortino:
0.066

Net maximum drawdown:
-59.58%

Net Calmar:
-0.052

Average turnover:
70.88%

Estimated cost drag:
0.59%

2x cost net CAGR:
-3.24%

2x cost net Sharpe:
0.069

Average holdings:
1.864

Average exposure:
32.93%

Time invested:
32.93%

CSM-only net CAGR:
-3.04%

CSM-only net Sharpe:
0.070

CSM-only max drawdown:
-59.24%

Frozen benchmark CAGR:
10.95%

Frozen benchmark Sharpe:
0.690

Frozen benchmark max drawdown:
-25.33%

First-third result:
0.00%

Middle-third result:
-9.41%

Final-third result:
-4.50%

TSM gate effect:
DEGRADED

Look-ahead check:
PASS

Backtest reproducibility:
PASS

Survivorship integrity:
PARTIAL

PIT integrity:
PARTIAL

Corporate-actions limitation:
OPEN

Alpha logic changed:
NO

Parameter optimization performed:
NO

Broker mutation calls:
0

Scientific T0 established:
NO

Formal alpha validated:
NO

Overall decision:
EXPLORATORY_EVIDENCE_UNPROMISING

PAPER-001 authorized:
NO

Real-money trading authorized:
NO

Production authorized:
NO

Authorized next action:
RESEARCH REVIEW / NO PAPER LAUNCH
```
