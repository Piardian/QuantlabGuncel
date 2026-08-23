# RRV-001 Failure Attribution Report

RRV-001 attributes EXB-002 sparse portfolio behavior to CSM eligibility mechanics under the frozen EXB-001 reduced Alpaca dataset.

No strategy return, Sharpe, drawdown, benchmark comparison, optimization, or new alpha logic was evaluated.

## Key Counts

| Metric | Value |
| --- | ---: |
| Rebalance dates | 56 |
| Dates passing CSM minimum eligible count | 20 |
| Dates failing CSM minimum eligible count | 36 |
| First threshold pass date | 2024-12-31 |
| Median final CSM eligible count | 47.0 |
| Average final CSM eligible count | 48.0 |
| Minimum final CSM eligible count | 41 |
| Maximum final CSM eligible count | 55 |

## Interpretation

The EXB-002 low-exposure result is primarily consistent with universe/data eligibility starvation rather than TSM gate suppression.

CSM formula defect identified: NO  
TSM primary cause: NO  
Portfolio engine defect identified: NO  
Universe/data eligibility primary suspect: YES  
CSM x TSM hypothesis rejected: NO
