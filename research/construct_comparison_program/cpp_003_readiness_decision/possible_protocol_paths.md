# CPP-003 Possible Protocol Paths

| path_id | path_name | classification | description |
| --- | --- | --- | --- |
| PATH-A | Defer CPP-003 under current protocol | VALID_UNDER_CURRENT_PROTOCOL | Do not run incremental information analysis. Mark CPP-003 as not eligible until all-construct common sample reaches N >= 756 using frozen outputs. |
| PATH-B | Proceed to CPP-004 using only eligible CPP-002 evidence | VALID_WITH_LIMITED_SCOPE | CPP-004 may use corrected CPP-002 pairwise evidence, but must explicitly exclude partial/multivariate evidence unavailable from CPP-003. |
| PATH-C | New preregistered alignment/remediation protocol | REQUIRES_NEW_PREREGISTRATION | A future protocol could define a different eligible construct subset, longer CRD-001 history source, or staged/common-sample families before analysis. It cannot be chosen after looking at statistical outcomes. |
| PATH-D | Use pairwise maximum samples for incremental analysis | NOT_ALLOWED_UNDER_CURRENT_PROTOCOL | CPP-000.5 permits pairwise maximum sample for pairwise dependence only, not multivariate/incremental analysis. |
| PATH-E | Forward-fill or impute missing construct outputs | NOT_ALLOWED_UNDER_CURRENT_PROTOCOL | CPP-000.5 forbids new forward fill or imputation during CPP unless already contained in frozen construct output. |

## Interpretation

Only PATH-A and PATH-B are valid under the current protocol. PATH-C requires a new preregistration before any analysis. PATH-D and PATH-E are not permitted under CPP-000.5.
