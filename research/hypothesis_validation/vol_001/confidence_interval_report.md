# Confidence Interval Report

## Bootstrap Confidence Intervals

Bootstrap method: resampling high and low VOL-001 buckets independently.

Iterations: 4000

hypothesis                  feature  difference    ci_low   ci_high        classification
        H1         abs_daily_return    0.007930  0.006961  0.008955 Supported by evidence
        H2     abs_overnight_return    0.005190  0.004537  0.005904 Supported by evidence
        H3 abs_open_to_close_return    0.005374  0.004669  0.006086 Supported by evidence
        H4             rs_component    0.000173  0.000143  0.000206 Supported by evidence
        H5                 drawdown   -0.062007 -0.067356 -0.056508 Supported by evidence
        H6   high_state_persistence    0.761588  0.174434  0.225033 Supported by evidence

## Boundary

Confidence intervals describe uncertainty in the observed historical sample. They do not establish causality.
