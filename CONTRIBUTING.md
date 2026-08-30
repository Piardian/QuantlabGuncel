# Contributing

QuantLab is a research-oriented codebase. Changes should preserve reproducibility and make research assumptions explicit.

## Development principles

- Keep data, strategy, execution simulation, and reporting concerns separated.
- Prefer configuration-driven experiments over hidden parameters.
- Add regression coverage when behavior changes.
- Document assumptions that can affect research results.
- Never commit API keys, credentials, private datasets, or generated sensitive artifacts.

## Commit convention

Use Conventional Commit style when possible:

```text
feat: add strategy component
fix: correct execution model
test: add regression coverage
refactor: simplify data layer
docs: update research methodology
ci: update validation workflow
chore: maintenance change
```

## Research changes

A research-related change should state:

1. The hypothesis or purpose
2. The data and configuration used
3. The implementation change
4. The validation performed
5. Known limitations

Backtest results should not be presented as guarantees of future performance.
