# Calibration Analysis

## Scope

LIQ-001 is a continuous construct, not a fitted probability model.

For diagnostic purposes only, percentile rank of `liq001_zscore` is compared against unconditional MR-STRESS occurrence using Brier score.

## Results

 horizon                   target  unconditional_event_rate  rank_score_brier  null_brier  brier_delta_vs_null
       5  future_mr_stress_any_5d                  0.229478          0.184624    0.176818             0.007807
      20 future_mr_stress_any_20d                  0.289979          0.177958    0.205891            -0.027933
      60 future_mr_stress_any_60d                  0.421375          0.188572    0.243818            -0.055246

## Interpretation

Calibration is not the primary strength of LIQ-001 in PV-001 because no probability model is fitted. The main predictive evidence is rank-based.
