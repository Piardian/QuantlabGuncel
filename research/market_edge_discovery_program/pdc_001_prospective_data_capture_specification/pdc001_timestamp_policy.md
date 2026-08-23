# Timestamp Policy

All system timestamps are stored in UTC.

Where available, distinguish:

- event_time
- source_time
- available_to_system_time
- ingestion_time

The system must answer separately:

```text
When did the event occur?
```

and:

```text
When could the research system first know it?
```

Late data must be marked and must not silently revise previous snapshots.
