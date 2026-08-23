# WOR-001: Workflow Out-of-Sample Reproducibility Protocol

## Background

The CSM-001 x TSM-001 composite workflow review completed through CWF-001.

Final CWF-001 classification:

**Scientifically Supported Nested Composite Workflow**

The supported structure was:

- TSM-001 supplies broad own-trend state context.
- CSM-001 identifies a narrower cross-sectional leadership subset inside that state.

## Purpose

WOR-001 registers the protocol for testing whether the nested composite workflow structure reproduces out of sample.

This stage does not execute the OOS study.

## Primary Research Question

Does the CSM-001 x TSM-001 nested workflow structure reproduce on data not used in the CWS-001 evaluation?

## Primary Hypothesis

H1:

The nested workflow relationship observed in CWS-001 reproduces out of sample: CSM_HIGH remains largely contained inside TSM_HIGH, while TSM_HIGH remains broader than CSM_HIGH.

## Null Hypothesis

H0:

The nested workflow relationship observed in CWS-001 does not reproduce out of sample.

## Frozen Inputs

The construct definitions and implementations remain frozen:

- CSM-001
- TSM-001

The in-sample reference evidence remains frozen:

- CIP-001
- CWP-001
- CWS-001
- CWF-001

## OOS Requirement

The OOS period must not overlap the CWS-001 evaluated sample.

CWS-001 evaluated:

2011-01-03 to 2025-12-30

Therefore WOR execution must use only dates after:

2025-12-30

If sufficient OOS data are unavailable, the execution stage must conclude:

**Inconclusive: Insufficient OOS Data**

## Forbidden

Do NOT:

- modify CSM-001
- modify TSM-001
- create a new construct
- optimize parameters
- tune thresholds
- evaluate trading performance
- claim alpha
- recommend production deployment
- use overlapping in-sample observations

## Authorized Next Stage

**WOR-002: Workflow Out-of-Sample Reproducibility Audit**
