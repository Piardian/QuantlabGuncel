# PEAD-001 / CD-001 Construct Definition

Purpose: freeze one precise, reproducible PEAD construct definition based on LR-001.

CD-001 must answer:

- Which earnings event definition will be used?
- Which surprise definition will be used?
- Which point-in-time data fields are required?
- How will announcement timing be handled?
- What is the first tradable price after announcement?
- Which observations are excluded for data safety?
- Which alternatives are rejected and why?

Decision priority:

Data integrity and look-ahead safety take priority over expected performance.

Forbidden:

- Backtesting
- Parameter optimization
- Profitability claims
- Production recommendations
- Using any data unavailable at the decision time
