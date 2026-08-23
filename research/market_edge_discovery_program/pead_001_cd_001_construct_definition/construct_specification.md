# Construct Specification

Construct:

**PEAD-001 Point-in-Time Analyst Surprise Post-Earnings Announcement Drift State**

Unit of observation:

Firm-quarter earnings announcement event.

Primary variable:

`standardized_earnings_surprise`

Formula:

```text
(actual_eps - consensus_expected_eps) / abs(price_reference)
```

State output:

```text
POSITIVE / NEGATIVE / NEUTRAL
```

Decision-time safety:

The state is not available until after the public announcement timestamp.

No return, alpha, drift window or trading action is part of the construct definition.
