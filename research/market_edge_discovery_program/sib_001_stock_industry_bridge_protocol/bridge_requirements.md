# Bridge Requirements

## Minimum Requirements

| Requirement | Required | Reason |
|---|---:|---|
| Point-in-time membership | Yes | Prevents future/current taxonomy leakage |
| Ticker-level coverage | Yes | Required to join with CSM-001 |
| Industry-level compatibility | Yes | Required to join with ISM-001 |
| Historical timestamp | Yes | Required for reproducible monthly alignment |
| Delisting/symbol-change handling | Yes | Prevents survivorship distortion |
| Deterministic mapping rule | Yes | Prevents discretionary assignment |
| Versioned source | Yes | Enables auditability |
| Missing-data policy | Yes | Prevents silent sample drift |

## Compatibility Target

The future bridge must create a valid panel with fields such as:

- `date` or `month`
- `ticker`
- `industry_id`
- `industry_taxonomy`
- `mapping_valid`
- `mapping_source`

## Scientific Standard

If a bridge cannot satisfy point-in-time requirements, it may not be used for confirmatory CSM x ISM interaction research.
