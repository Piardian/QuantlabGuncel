# OPT-001 / CV-001

# Stress Episode Review

## Purpose

This is a descriptive face-validity review. It does not evaluate prediction, economic value, or trading performance.

## Top Raw VIX Observations

| date | opt001_vix_close | opt001_zscore_252d | opt001_percentile_252d | opt001_data_quality_flag |
| --- | --- | --- | --- | --- |
| 2020-03-16 | 82.690000 | 7.637809 | 1.000000 | OK |
| 2008-11-20 | 80.860000 | 3.545089 | 1.000000 | OK |
| 2008-10-27 | 80.060000 | 4.909934 | 1.000000 | OK |
| 2008-10-24 | 79.130000 | 5.093225 | 1.000000 | OK |
| 2020-03-18 | 76.450000 | 5.854943 | 0.996032 | OK |
| 2020-03-17 | 75.910000 | 6.268315 | 0.996032 | OK |
| 2020-03-12 | 75.470000 | 8.326319 | 1.000000 | OK |
| 2008-11-19 | 74.260000 | 3.186293 | 0.992063 | OK |
| 2008-11-21 | 72.670000 | 2.918231 | 0.984127 | OK |
| 2020-03-19 | 72.000000 | 5.105067 | 0.984127 | OK |

## Largest High-Percentile Episodes

Episodes are contiguous clusters of OK observations where `opt001_percentile_252d >= 0.95`, allowing short calendar gaps between trading observations.

| episode_id | start | end | observations | max_vix | mean_vix | max_zscore | mean_percentile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 88 | 2020-02-24 | 2020-03-30 | 26 | 82.690000 | 52.937692 | 8.326319 | 0.989469 |
| 65 | 2008-09-15 | 2008-11-21 | 43 | 80.860000 | 55.579767 | 6.632213 | 0.986342 |
| 66 | 2008-12-01 | 2008-12-01 | 1 | 68.510000 | 68.510000 | 2.482176 | 0.956349 |
| 103 | 2025-04-03 | 2025-04-22 | 13 | 52.330000 | 36.479231 | 6.870581 | 0.981074 |
| 69 | 2011-08-04 | 2011-09-13 | 23 | 48.000000 | 37.168696 | 7.807579 | 0.979469 |
| 67 | 2010-05-06 | 2010-06-09 | 16 | 45.790000 | 35.924375 | 4.756965 | 0.981647 |
| 37 | 1998-09-30 | 1998-10-09 | 8 | 45.740000 | 42.545000 | 2.953014 | 0.981151 |
| 70 | 2011-09-21 | 2011-10-04 | 10 | 45.450000 | 40.580000 | 3.243136 | 0.971429 |
| 36 | 1998-08-14 | 1998-09-21 | 17 | 45.290000 | 39.381765 | 4.252166 | 0.982960 |
| 49 | 2002-07-15 | 2002-08-07 | 14 | 45.080000 | 39.315714 | 3.585923 | 0.974348 |

## Interpretation

The largest VIX observations and high-percentile clusters occur around recognizable market stress windows. This supports the interpretation that OPT-001 behaves as an options-implied volatility state sensor. This does not imply predictive ability or economic value.
