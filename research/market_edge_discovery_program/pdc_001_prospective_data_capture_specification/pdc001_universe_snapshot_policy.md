# Universe Snapshot Policy

## Frequency

Capture universe/security-master state once per US equity trading day after official close/final source publication.

## Timezone

Store timestamps in UTC. Preserve source timezone where provided.

## Snapshot Timing

Draft target:

`Post-close after end-of-day data finalization`

## Retry Behavior

Failed or partial snapshots produce a failure manifest and may be retried. Retry artifacts must not overwrite original failed artifacts.

## Blocker

The exact source finalization time is unresolved because source access is unresolved.
