# Data Lineage

## CSM Score

```text
Yahoo-derived adjusted close panel
  -> output/csm_001_cv001/adjusted_close_panel.csv
  -> lagged 12-1 adjusted-close return
  -> cross-sectional percentile rank
  -> csm001_top_decile_flag
  -> output/csm_001_cv001/csm001_construct_state.csv
  -> frozen hash in BFL-001
```

## TSM State

```text
Yahoo-derived adjusted close panel
  -> output/csm_001_cv001/adjusted_close_panel.csv
  -> lagged 12-1 own-history return
  -> tsm001_positive_state
  -> output/tsm_001_cv001/tsm001_construct_state.csv
  -> frozen hash in BFL-001
```

## Portfolio Accounting

```text
CSM state + TSM state
  -> CSM_HIGH x TSM_POSITIVE selected state
  -> monthly signal at first trading day rebalance close
  -> next trading day close return measurement
  -> WPC-002 gross equal-weight portfolio series
  -> frozen hash in BFL-001
```
