# V2 Candidate Data Lineage

## Status

No V2 candidate data lineage was produced.

## Reason

Critical remediation blockers remain unresolved:

- No point-in-time historical universe membership source found.
- No survivorship-aware delisted-security source found.

## V1 Lineage Preserved

```text
Yahoo-derived adjusted close panel
  -> CSM 12-1 cross-sectional state
  -> TSM 12-1 own-trend state
  -> CSM_HIGH x TSM_POSITIVE workflow state
  -> WPC-002 gross equal-weight research portfolio
```

## V2 Required Future Lineage

```text
PIT universe and security lifecycle source
  -> survivorship-aware price panel
  -> verified corporate-action adjusted price panel
  -> frozen CSM logic unchanged
  -> frozen TSM logic unchanged
  -> frozen CSM x TSM workflow unchanged
  -> BFL-002 candidate artifacts
```
