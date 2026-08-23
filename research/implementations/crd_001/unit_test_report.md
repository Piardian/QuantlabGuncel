# Unit Test Report

Executed checks:

1. PASS: Source frame parsing accepts FRED-style DATE and BAMLH0A0HYM2 columns.
2. PASS: Business-day indexing and 5-calendar-day forward-fill policy follow CD-001.
3. PASS: Gaps longer than 5 calendar days are marked invalid.
4. PASS: 252-valid-observation z-score and percentile columns are present.
5. PASS: Data-quality flags follow the frozen schema.
6. PASS: Repeated execution on identical synthetic input is deterministic.

Note: `pytest` is not installed in the local virtual environment, so the test functions were executed directly with Python.
