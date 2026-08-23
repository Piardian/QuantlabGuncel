# EXB-001 Execution Timing Policy

## Frozen Timing Policy

1. Data through date T close may be used only after T close.
2. Any exploratory order decision generated from T close data may execute no earlier than the next trading session.
3. Same-bar execution is forbidden.
4. Intraday information is not used.
5. Future bars are forbidden.

## Intended Bias Control

This policy is designed to prevent same-day close look-ahead and future information leakage during EXB-002.

## Scope

This is an exploratory timing policy. It does not certify live execution realism.
