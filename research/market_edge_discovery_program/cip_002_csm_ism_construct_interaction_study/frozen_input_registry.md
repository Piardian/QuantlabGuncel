# Frozen Input Registry

## Study

CIP-002: CSM-001 x ISM-001 Construct Interaction Study

## Frozen Inputs Reviewed

### CSM-001

Source state file:

`output/csm_001_cv001/csm001_construct_state.csv`

Observation unit:

**Ticker-date**

Relevant frozen fields:

- `date`
- `ticker`
- `csm001_momentum_score`
- `csm001_top_decile_flag`
- `csm001_valid_observation`

### ISM-001

Source state file:

`output/ism_001/ism001_industry_momentum_state.csv`

Observation unit:

**Industry-month**

Relevant frozen fields:

- `month`
- `industry_id`
- `industry_name`
- `ism_score`
- `ism_state`
- `ism_valid_observation`

## Frozen ISM-001 Limitations

ISM-001 CD-001 explicitly states:

- ISM-001 is industry-level, not stock-level.
- It does not assign industries to individual stocks.
- It does not use point-in-time GICS/SIC/NAICS membership.
- Current Yahoo industry classifications, current GICS labels, current SIC/NAICS labels and manually assigned sector labels are explicitly excluded.

ISM-001 FSR-001 states:

- `stock_level_applicability`: `Not supported`

## Registry Decision

CIP-002 may not create or infer ticker-to-industry membership because doing so would modify the frozen evidence boundary.

Therefore, direct CSM_HIGH x ISM_HIGH interaction cells are not empirically estimable from the frozen artifacts.
