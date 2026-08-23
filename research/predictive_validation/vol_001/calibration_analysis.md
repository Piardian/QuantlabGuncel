# Calibration Analysis

## Scope

VOL-001 is a continuous construct, not a fitted probability model.

For diagnostic purposes only, percentile rank of `vol001_zscore` is compared against future high-volatility occurrence using Brier score.

## Results

 horizon                  target  unconditional_event_rate  rank_score_brier  null_brier  brier_delta_vs_null
       5  future_high_vol_any_5d                  0.227079          0.163545    0.175514            -0.011969
      20 future_high_vol_any_20d                  0.311567          0.169279    0.214493            -0.045214
      60 future_high_vol_any_60d                  0.468017          0.198882    0.248977            -0.050095

## Interpretation

Calibration is not the primary claim in PV-001 because no probability model is fitted. The main predictive evidence is rank-based.
