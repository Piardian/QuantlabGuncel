# Use Case Registry

## UC-1: CSM Gated By TSM-Positive State

Question:

Does requiring CSM_HIGH observations to also be TSM_HIGH improve or preserve economic outcomes relative to CSM_HIGH alone?

Important note:

CIP/CWS/WOR found CSM_HIGH was already nested inside TSM_HIGH in evaluated samples. Therefore UC-1 may show no change. That outcome must be reported as evidence, not treated as failure.

## UC-2: CSM Weighted By TSM State

Question:

Does TSM state provide useful weighting context for CSM-selected observations?

Allowed weights:

- TSM_HIGH: 1.0
- TSM_LOW: 0.0

No alternative weights may be introduced.

## UC-3: TSM Context Versus CSM Leadership Subset

Question:

Does the narrower CSM_HIGH subset inside TSM_HIGH differ economically from the broader CSM_NOT_HIGH x TSM_HIGH region?

This is a workflow utility question, not a construct redefinition.

## UC-4: Conflict-Region Handling Audit

Question:

Can the workflow evaluate conflict regions such as CSM_HIGH x TSM_LOW?

Expected limitation:

If the conflict region remains absent or too small, UC-4 must conclude Inconclusive.
