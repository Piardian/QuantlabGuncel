# PV-001 Predictive Validation

## Question
Does the identified trend-related construct demonstrate statistically credible predictive validity under the preregistered evaluation protocol?

## Primary result
- Composite trend proxy OOS AUC: 0.4717
- Composite trend proxy OOS rank IC: -0.0554
- Composite trend proxy top-decile minus bottom-decile mean R: -0.1594
- Composite trend proxy calibration slope: -0.0208

## Sensitivity check
- Trend strength proxy OOS AUC: 0.4982
- Trend strength proxy OOS rank IC: 0.0020
- Trend strength proxy top-decile minus bottom-decile mean R: 0.0273

## Confidence intervals
        score_variant              metric  estimate    ci_low   ci_high bootstrap_method  iterations
COMPOSITE_TREND_PROXY                 auc  0.471680  0.456613  0.486394     year_cluster        4000
COMPOSITE_TREND_PROXY                  ic -0.055404 -0.079456 -0.033053     year_cluster        4000
COMPOSITE_TREND_PROXY          lift_avg_R -0.159437 -0.299432 -0.025076     year_cluster        4000
COMPOSITE_TREND_PROXY   calibration_slope -0.020809 -0.028781 -0.012150     year_cluster        4000
COMPOSITE_TREND_PROXY    top_decile_avg_R -0.019340 -0.089468  0.031119     year_cluster        4000
COMPOSITE_TREND_PROXY bottom_decile_avg_R  0.140097  0.018088  0.277560     year_cluster        4000
 TREND_STRENGTH_PROXY                 auc  0.498203  0.485558  0.511873     year_cluster        4000
 TREND_STRENGTH_PROXY                  ic  0.002044 -0.024781  0.029361     year_cluster        4000
 TREND_STRENGTH_PROXY          lift_avg_R  0.027324 -0.159647  0.247271     year_cluster        4000
 TREND_STRENGTH_PROXY   calibration_slope  0.000198 -0.004775  0.005176     year_cluster        4000
 TREND_STRENGTH_PROXY    top_decile_avg_R  0.038342 -0.100015  0.186535     year_cluster        4000
 TREND_STRENGTH_PROXY bottom_decile_avg_R  0.011017 -0.164085  0.149346     year_cluster        4000

## Interpretation standard
- Supported by evidence: the metric remains positive and stable OOS with non-trivial separation.
- Not supported by evidence: the metric is near-null, unstable, or does not survive OOS.
- Inconclusive: evidence is directionally positive but too small or too unstable for a firm conclusion.
- Speculation: any statement beyond the observed OOS metrics and their uncertainty.

## Current conclusion
Predictive validity is not supported by evidence for the composite trend proxy; the OOS separation is too weak to distinguish it from the null.