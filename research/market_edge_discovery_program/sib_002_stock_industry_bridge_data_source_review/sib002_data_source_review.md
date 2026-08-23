# SIB-002: Stock-to-Industry Bridge Data Source Review

## Purpose

Review candidate data sources for a future point-in-time stock-to-industry bridge that could validly connect CSM-001 ticker-level observations to ISM-001 Ken French 49 industry-month states.

No bridge was implemented in this stage.

## Final Decision

**CONDITIONAL GO**

## Rationale

A scientifically plausible bridge path exists:

**point-in-time stock identifier data + historical SIC code + Ken French SIC-to-49-industry mapping**

However, this project does not yet have confirmed access to a validated point-in-time CRSP/Compustat-style security master with historical SIC coverage.

Therefore SIB-003 may proceed only if the required source data can be obtained and documented before implementation.

## Reviewed Candidate Source Families

1. CRSP / Compustat historical SIC path.
2. Ken French 49 industry SIC definitions.
3. GICS History.
4. Current metadata sources.
5. Manual ticker-to-industry assignment.

## Evidence Summary

Supported by evidence:

- Ken French 49 industry portfolios are based on SIC-code assignment rules.
- CRSP/Compustat-style datasets may provide historical identifiers and SIC classifications.
- S&P Global offers GICS History with active and inactive classifications from 1985 forward.

Not supported:

- Current metadata sources are not adequate for confirmatory historical research.
- Manual mapping is not scientifically acceptable.
- GICS History directly maps into Ken French 49 industries without a separate translation layer.

## Decision

SIB-002 authorizes a conditional next stage:

**SIB-003: Bridge Definition**

SIB-003 must define a bridge only if a valid point-in-time source can be specified.

If no such source is available, the bridge program must stop with NO GO before implementation.

## Sources Used

- Kenneth French Data Library, 49 Industry Portfolio construction details: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html
- Kenneth French Data Library, industry definition changes: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/changes_ind.html
- S&P Global Marketplace, GICS dataset overview: https://www.marketplace.spglobal.com/en/datasets/gics-%2890%29
- MSCI GICS methodology and taxonomy overview: https://www.msci.com/indexes/index-resources/gics
- CRSP documentation reference surfaced through WRDS search results: https://wrds-www.wharton.upenn.edu/documents/413/CRSPAccess_Software_Guide.pdf
