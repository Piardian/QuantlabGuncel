# Implementation Requirements

IM-001 must implement:

- Event dataset loader.
- Point-in-time consensus validation.
- Announcement timing parser.
- First valid decision timestamp assignment.
- Surprise calculation.
- State assignment.
- Exclusion report.
- Reproducibility report.

IM-001 must abort if required point-in-time fields are absent.

No fallback to unsafe revised estimates is allowed.
