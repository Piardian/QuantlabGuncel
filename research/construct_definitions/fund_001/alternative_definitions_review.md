# FUND-001 / CD-001

# Alternative Definitions Review

## Accepted Definition

```text
US Financial Commercial Paper Funding Spread Stress
```

Defined as:

```text
DCPF3M - DTB3
```

## Alternative 1: LIBOR-OIS Spread

Decision: Rejected.

Rationale:

- strong historical usage,
- but LIBOR discontinuation creates modern reproducibility problems,
- LIBOR may not reliably represent bank funding costs across recent periods,
- high contamination from counterparty credit risk.

## Alternative 2: TED Spread

Decision: Rejected.

Rationale:

- historically prominent crisis indicator,
- but LIBOR dependency creates continuity issues,
- interpretation mixes bank credit risk, liquidity risk, and safe-asset demand.

## Alternative 3: SOFR-Based Funding Spread

Decision: Rejected for FUND-001 CD-001.

Rationale:

- more modern than LIBOR,
- but candidate spread selection is not yet sufficiently standardized for this construct,
- may require additional design choices not justified at this stage.

This may be a future FUND variant.

## Alternative 4: Repo / Secured Funding Stress

Decision: Rejected.

Rationale:

- theoretically attractive,
- closely related to collateral funding stress,
- but clean long-history public daily data is harder to obtain and standardize.

This may be a future secured-funding construct.

## Alternative 5: Haircut / Margin Stress

Decision: Rejected.

Rationale:

- highly aligned with funding-liquidity spiral theory,
- but direct public daily data availability is limited.

## Alternative 6: Dealer Balance-Sheet Funding Capacity

Decision: Rejected.

Rationale:

- theoretically important,
- but lower frequency, reporting lag, and implementation complexity make it less suitable as the first FUND-001 construct.

## Alternative 7: OFR FSI Funding Category

Decision: Rejected.

Rationale:

- institutionally recognized,
- but composite methodology may mix multiple funding-related signals,
- CD-001 prioritizes a narrow transparent construct.

## Alternative 8: Chicago Fed NFCI Components

Decision: Rejected.

Rationale:

- useful broad financial conditions reference,
- but not a pure funding-stress construct,
- may overlap materially with risk, credit, leverage, volatility, and liquidity constructs.

## Alternative 9: Central-Bank Liquidity Operations

Decision: Rejected.

Rationale:

- strong academic measurement precedent in some jurisdictions,
- but less directly applicable to a US market sensor built from public daily market data.

## Summary

The selected definition is not the theoretically purest possible funding-stress measure. It is selected because it is narrow, public, reproducible, interpretable, non-LIBOR-based, and directly tied to short-term financial funding costs.

