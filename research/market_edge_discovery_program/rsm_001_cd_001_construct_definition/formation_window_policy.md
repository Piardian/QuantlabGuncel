# Formation Window Policy

RSM-001 uses a 12-1 residual momentum formation window.

For month `t`:

- Include residual returns from `t-12` through `t-2`.
- Exclude residual return from `t-1`.
- Exclude month `t` because it is the evaluation month.

Rationale:

The 12-1 design aligns with canonical intermediate-horizon momentum conventions and avoids the most recent month.

No alternative formation window may be used without restarting CD.
