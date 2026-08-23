# STEP-2 Strategy Hash Specification

## Strategy Identification
- Strategy ID: `CSM001_TSM001`
- Universe ID: `FUF001_FREE_US_EQUITY_250_V1`

## Deterministic Fingerprint Components
The frozen strategy configuration includes:
1. `strategy_id`: `CSM001_TSM001`
2. `csm_lookback`: `252`
3. `csm_skip`: `21`
4. `csm_ranking`: `percentile`
5. `min_eligible`: `50`
6. `tsm_lookback`: `252`
7. `tsm_threshold`: `0.0`
8. `tsm_state_mapping`: `binary`
9. `csm_tsm_interaction`: `multiplicative_gate`
10. `rebalance`: `monthly`
11. `portfolio_weighting`: `equal_weight_top_decile`
12. `execution_timing`: `t_plus_1_open`

## Hashing Method
JSON serialization with sorted keys (`json.dumps(config, sort_keys=True, separators=(",", ":"))`) followed by SHA256 digest in uppercase hexadecimal.
