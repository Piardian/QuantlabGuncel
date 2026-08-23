# WEV-001: Workflow Economic Validation Protocol

## Background

The CSM-001 x TSM-001 nested composite workflow has completed:

- CIP-001: Partially Complementary
- CWP-001: Protocol Registered
- CWS-001: Workflow Supported
- CWF-001: Scientifically Supported Nested Composite Workflow
- WOR-001: OOS Reproducibility Protocol
- WOR-002: Reproduced

The workflow has scientific support and out-of-sample reproducibility. Economic utility has not been evaluated.

## Purpose

WEV-001 registers the protocol for evaluating whether the reproduced CSM-001 x TSM-001 nested composite workflow has measurable economic utility in predefined decision workflows.

This is a protocol registration stage only.

No empirical economic analysis is performed in WEV-001.

## Primary Research Question

Does the CSM-001 x TSM-001 nested composite workflow provide measurable economic utility relative to predefined benchmark workflows?

## Economic Validation Scope

The evaluation must remain limited to predefined workflow-level applications.

The workflow is not a new construct and must not be presented as a production-ready trading strategy.

## Predefined Use Cases

UC-1:

CSM-only benchmark versus CSM gated by TSM-positive state.

UC-2:

CSM-only benchmark versus CSM weighted by TSM state.

UC-3:

TSM-positive universe context versus CSM leadership subset inside TSM-positive state.

UC-4:

Conflict-region handling audit, limited to descriptive treatment because CSM_HIGH x TSM_LOW has been rare or absent.

No additional use case may be introduced after execution begins.

## Frozen Inputs

Use only frozen outputs from:

- CSM-001
- TSM-001
- CWS-001
- WOR-002

No construct definition, parameter or threshold may be modified.

## Benchmarks

Benchmark A:

CSM-001 standalone workflow using frozen CSM_HIGH state.

Benchmark B:

TSM-001 standalone state workflow using frozen TSM_HIGH state.

Benchmark C:

Equal-weight eligible universe benchmark.

Benchmark D:

Static top-decile CSM benchmark without TSM interaction.

All benchmarks must be defined before execution and must not be optimized.

## Allowed Metrics

Economic utility may be evaluated using:

- Mean forward return
- Median forward return
- Hit rate
- Volatility of forward returns
- Downside deviation
- Max observed forward drawdown proxy
- Turnover proxy
- Coverage
- State availability
- Benchmark-relative spread
- Stability across years

If portfolio returns are evaluated, they must use fixed, preregistered equal-weight workflow portfolios only.

## Forbidden

Do NOT:

- optimize parameters
- tune thresholds
- change CSM-001
- change TSM-001
- create a new construct
- search for best holding period
- add transaction-cost assumptions after seeing results
- recommend production deployment
- claim alpha beyond the evaluated workflow evidence
- perform portfolio optimization

## Decision Categories

WEV-002 must conclude exactly one:

- Economic Utility Supported
- Economic Utility Partially Supported
- Economic Utility Not Supported
- Inconclusive

## Authorized Next Stage

**WEV-002: Workflow Economic Validation**
