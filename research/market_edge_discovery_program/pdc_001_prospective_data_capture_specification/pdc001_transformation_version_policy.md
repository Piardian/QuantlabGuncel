# Transformation Version Policy

Each raw-to-normalized transformation must record:

- transformation_id
- code hash or commit hash
- configuration version
- input hashes
- output hashes
- execution timestamp
- warnings/errors

Same raw input and same transformation version must produce deterministic output.
