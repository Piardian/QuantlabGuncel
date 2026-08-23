# Bias Risk Register

## Primary Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Current-classification look-ahead | High | Require point-in-time historical membership |
| Survivorship bias | High | Require delisted/security history policy |
| Taxonomy mismatch | High | Define mapping to Ken French 49 or explicitly validate translation |
| Manual assignment discretion | High | Require deterministic documented mapping |
| Symbol-change errors | Medium | Require stable security identifier policy |
| Missing industry history | Medium | Require missing-data policy |
| Data vendor revision risk | Medium | Store source version and hash |

## Forbidden Bias-Prone Practices

- Assigning industries from present-day metadata.
- Manually mapping ambiguous tickers after observing results.
- Dropping hard-to-map securities without reporting coverage impact.
- Mixing taxonomies without a predefined translation rule.
