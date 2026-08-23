# DVB-001 Minimum Purchase Requirements

A vendor or source stack may proceed to SLA-002 only if the owner can provide real access and license evidence for the following.

## Required Evidence

| Requirement | Needed For SLA-002 |
|---|---|
| Account status | active account or entitlement evidence |
| Authentication | API key/token/credential available through secure local mechanism |
| Market data product | product/dataset name and entitlement |
| Security master product | product/dataset name and entitlement |
| Corporate-action product | product/dataset name and entitlement |
| License document | ToS, agreement, contract, or written vendor clarification |
| Local storage permission | explicit or documented allowance |
| Automated retrieval permission | explicit or documented allowance |
| Research use permission | explicit or documented allowance |
| Post-subscription retention | explicit or documented status |
| Price/cost | subscription or usage budget understood |

## Credential Safety

Credentials must not be pasted into reports.

Preferred mechanisms:

- environment variable
- local untracked `.env`
- secure secret manager
- vendor CLI authenticated session

Reports may record credential mechanism and entitlement status only.

