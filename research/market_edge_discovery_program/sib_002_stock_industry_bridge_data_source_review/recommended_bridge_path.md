# Recommended Bridge Path

## Preferred Path

Use point-in-time historical SIC classification and map SIC codes into Ken French 49 industry buckets.

## Proposed Future Bridge Fields

A future bridge artifact should contain:

- `month`
- `ticker`
- `security_id`
- `sic_code`
- `ff49_industry_id`
- `ff49_industry_name`
- `classification_source`
- `classification_date`
- `mapping_valid`

## Required Future Validation

Before use in CIP research:

- coverage by month
- ticker match rate
- delisting/symbol-change policy
- SIC-to-FF49 mapping verification
- deterministic hash
- missing-data report
- look-ahead safety audit

## Boundary

This is a recommended data-source path, not an implemented bridge.
