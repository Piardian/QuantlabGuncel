# Resume Requirements

## Required Data

To resume this branch, provide a point-in-time stock-level industry classification source with:

- historical security identifier
- ticker or tradable symbol history
- classification date
- SIC, GICS or equivalent industry code
- delisting / inactive security handling if available
- data dictionary
- source provenance
- coverage period

## Preferred Source

Preferred:

- CRSP/Compustat historical SIC/security master.

Acceptable alternative:

- Point-in-time GICS History, only if a separate translation layer to Ken French 49 is preregistered and validated.

## Not Acceptable

- Current Yahoo metadata.
- Current GICS/SIC/NAICS snapshots.
- Manual labels.
- Post-hoc ticker classification.

## Next Stage After Data Acquisition

Resume at:

**SIB-003-R: Bridge Definition Restart**

Do not proceed directly to implementation.
