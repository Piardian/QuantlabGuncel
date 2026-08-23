# Research Experiment Framework Design

The framework separates production behaviour from research controls.

```text
Production strategy defaults
        |
        +-- unchanged production execution
        |
ResearchExperimentConfig -> component overrides -> strategy parameters -> manifest
```

The strategy contains only generic component toggles. Experiment identity, notes,
datasets, universe definitions, output directories and manifests live in `research/`.
All toggles default to the current production behaviour.
