PAPER-001 STEP-3A.2 REPORT

- Eligible securities: 250
- Valid 12-1 returns: 250
- Rank min: 0.0
- Rank median: 0.5
- Rank max: 1.0
- Rank >= 0.90: 25
- Actual CSM candidates: 250
- TSM-approved candidates: 250
- Non-zero target weights: 250
- Candidate threshold invariant: FAIL
- Target consumes candidate set correctly: FAIL
- Root cause: Target portfolio construction currently passes all universe members or fallback equal weighting without strictly filtering out non-candidates.
- Alpha logic defect: YES
- Broker mutation calls: 0
- Performance evaluated: NO
- Decision: CSM_TECHNICAL_REMEDIATION_REQUIRED
