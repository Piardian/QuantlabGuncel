# Experiment Manifest Schema

Each `experiment_manifest.json` contains experiment ID, description, version,
timestamp, configuration hash, enabled/disabled component overrides, strategy
parameters, dataset, universe, time range, random seed and Python version.

The configuration hash is a SHA-256 hash of the canonical typed config payload.
