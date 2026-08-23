# CIP-002: CSM-001 x ISM-001 Construct Interaction Study

## Mission

Determine whether company-level leadership and industry-level leadership provide overlapping, incremental, or complementary scientific information.

## Frozen Constructs

CSM-001:

- Construct type: Cross-sectional company-level leadership.
- Observation unit: ticker-date.
- Frozen state file: `output/csm_001_cv001/csm001_construct_state.csv`

ISM-001:

- Construct type: Industry-level leadership.
- Observation unit: Ken French industry-month.
- Frozen state file: `output/ism_001/ism001_industry_momentum_state.csv`

## Final Conclusion

**Inconclusive**

## Why The Study Is Inconclusive

The requested interaction matrix requires a common observation unit.

Specifically, each CSM ticker-date or ticker-month observation would need to be assigned to a contemporaneous ISM industry state.

The frozen ISM-001 construct does not provide that mapping.

ISM-001 CD-001 explicitly states:

- ISM-001 is industry-level, not stock-level.
- It does not assign industries to individual stocks.
- It does not use point-in-time GICS/SIC/NAICS membership.
- Current Yahoo classifications, current GICS labels, current SIC/NAICS labels and manual labels are excluded.

ISM-001 FSR-001 further states:

- `stock_level_applicability`: `Not supported`

## Required Analyses Status

| Required analysis | Status | Reason |
|---|---|---|
| Information overlap analysis | Not evaluated | No common observation unit |
| Incremental information analysis | Not evaluated | No frozen ticker-to-industry bridge |
| Conditional predictive analysis | Not evaluated | No valid matched CSM x ISM panel |
| Interaction-state analysis | Not evaluated | CSM_HIGH x ISM_HIGH cells cannot be formed |
| Agreement / disagreement matrix | Not evaluated | No common binary state universe |
| Hierarchical leadership analysis | Inconclusive | Hierarchy requires stock-to-industry assignment |
| Conflict-region assessment | Not evaluated | Conflict states cannot be defined |
| Robustness analysis | Not evaluated | Base interaction panel unavailable |
| Scientific interpretation | Completed | Evidence boundary documented |

## Evidence Classification

Supported by evidence:

- CSM-001 and ISM-001 are completed frozen constructs.
- They operate at different observation units.
- ISM-001 does not currently support stock-level assignment.
- Direct CSM x ISM interaction analysis is not valid from the existing frozen artifacts.

Not supported by evidence:

- ISM-001 contributes incremental information beyond CSM-001.
- CSM-001 contributes incremental information beyond ISM-001.
- CSM-001 and ISM-001 are complementary.
- CSM-001 and ISM-001 are redundant.
- A hierarchical leadership workflow is justified.

Speculation:

- A future point-in-time taxonomy bridge might allow company-level and industry-level leadership to be studied together.

## Scientific Boundary

CIP-002 does not change the status of CSM-001 or ISM-001.

The correct scientific finding is not that the interaction failed.

The correct finding is that the current frozen evidence set is insufficient to estimate the interaction without introducing a new construct-interface assumption.
