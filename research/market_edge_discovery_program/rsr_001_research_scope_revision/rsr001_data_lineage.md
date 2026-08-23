# RSR-001 Data Lineage

## Existing V1 Lineage

```text
Yahoo-derived adjusted close panel
  -> current-style ticker panel
  -> CSM state
  -> TSM state
  -> CSM x TSM workflow
  -> exploratory historical baseline
```

Classification:

`EXPLORATORY_ONLY`

## Selected Prospective Lineage

```text
predefined T0
  -> universe/security snapshot
  -> market data snapshot
  -> corporate-action snapshot
  -> immutable raw artifact hashes
  -> frozen transformation config
  -> future research dataset
```

Classification:

`LIMITED_RESEARCH_CANDIDATE`
