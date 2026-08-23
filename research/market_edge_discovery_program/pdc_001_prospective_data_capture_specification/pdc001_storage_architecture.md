# Storage Architecture

Draft root:

`data/prospective/us_equities/`

Layout:

```text
raw/
normalized/
derived/
manifests/
schemas/
logs/
quarantine/
```

Raw files must be immutable. Corrected source deliveries create new versions rather than replacing prior files.

Blocker:

Write-once enforcement is not implemented yet.
