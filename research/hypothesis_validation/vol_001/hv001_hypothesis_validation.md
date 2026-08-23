# VOL-001 / HV-001: Hypothesis Validation

## Purpose

Evaluate whether the mechanism hypotheses generated in MI-001 are empirically supported.

This stage evaluates explanatory validity only. No predictive, alpha, profitability, trading-performance, or economic utility claim is made.

## Overall Classification

**Supported by evidence**

## Results

hypothesis                                                                    description                  feature expected_direction  high_count  low_count  high_mean  low_mean  difference    ci_low   ci_high  cohens_d  permutation_pvalue        classification
        H1                 High VOL-001 states have larger absolute daily market returns.         abs_daily_return           positive         751        751   0.012529  0.004599    0.007930  0.006961  0.008955  0.803599             0.00025 Supported by evidence
        H2                    High VOL-001 states have larger absolute overnight returns.     abs_overnight_return           positive         751        751   0.007783  0.002593    0.005190  0.004537  0.005904  0.756511             0.00025 Supported by evidence
        H3                High VOL-001 states have larger absolute open-to-close returns. abs_open_to_close_return           positive         751        751   0.009130  0.003756    0.005374  0.004669  0.006086  0.766247             0.00025 Supported by evidence
        H4              High VOL-001 states have higher Rogers-Satchell range components.             rs_component           positive         751        751   0.000198  0.000025    0.000173  0.000143  0.000206  0.560143             0.00025 Supported by evidence
        H5                         High VOL-001 states occur in deeper drawdown contexts.                 drawdown           negative         751        751  -0.084960 -0.022953   -0.062007 -0.067356 -0.056508 -1.134324             0.00025 Supported by evidence
        H6 High VOL-001 states exhibit persistence consistent with volatility clustering.   high_state_persistence           positive         751       3002   0.961385  0.199796    0.761588  0.174434  0.225033       NaN             0.00025 Supported by evidence

## Interpretation

The evidence supports the MI-001 mechanism that VOL-001 represents realized market turbulence. High VOL-001 states are associated with larger daily movement, larger overnight movement, larger intraday movement, higher range-based variation, deeper drawdown context, and persistent high-volatility episodes.

The evidence is not interpreted as prediction or economic utility.
