# GOAL

Begin:

WLC-002

Workflow Liquidity and Capacity Audit

CSM-001 x TSM-001

Mission
-------

WLC-001 registered the protocol for testing whether the WEV-002/WER-002-supported UC-3 workflow has sufficient selected-name liquidity and capacity.

This is NOT production deployment.

This is NOT portfolio optimization.

--------------------------------------------------

Primary Research Question

Does the UC-3 workflow have sufficient selected-name liquidity and capacity under predefined account-size and participation assumptions?

--------------------------------------------------

Scope

Evaluate only:

UC-3:

CSM leadership subset inside TSM_HIGH versus broader TSM-positive non-CSM region.

--------------------------------------------------

Required Analyses

1. Frozen input verification
2. OHLCV data availability check
3. UC-3 selected-name reconstruction
4. Dollar-volume feature calculation
5. Liquidity threshold pass-rate analysis
6. Account-size capacity analysis
7. Participation-limit analysis
8. OOS liquidity/capacity check
9. Missing-data analysis
10. Final liquidity/capacity classification

--------------------------------------------------

Forbidden

Do NOT:

- optimize universe membership
- exclude names after seeing liquidity results
- tune thresholds
- modify CSM-001
- modify TSM-001
- modify UC-3
- recommend production deployment
- claim live readiness

--------------------------------------------------

Allowed Conclusions

Exactly one:

- Liquidity Capacity Supported
- Liquidity Capacity Partially Supported
- Liquidity Capacity Not Supported
- Inconclusive
