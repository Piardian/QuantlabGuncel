# Executive Summary

CIP-001 evaluated whether frozen CSM-001 and TSM-001 provide complementary information when observed on the same ticker-date panel.

Overall conclusion: **Partially Complementary**.

Key evidence:

- Jaccard similarity between CSM_HIGH and TSM_HIGH: **0.1397**.
- Precision, P(TSM_HIGH | CSM_HIGH): **1.0000**.
- Recall, P(CSM_HIGH | TSM_HIGH): **0.1397**.
- TSM incremental R-squared beyond CSM at 21 trading days: **0.00181983**.
- CSM incremental R-squared beyond TSM at 21 trading days: **0.00098304**.

Interpretation:

CSM_HIGH observations are almost always TSM_HIGH, so the high-leadership CSM state is nested inside the positive own-trend region. However, TSM_HIGH covers a much broader region than CSM_HIGH. The evidence therefore does not support treating the two constructs as independent equivalents. It supports a partially complementary relationship in which TSM contributes broad own-trend state context while CSM contributes narrower cross-sectional leadership selection.

No conclusion is made regarding production deployment, alpha, or portfolio optimization.
