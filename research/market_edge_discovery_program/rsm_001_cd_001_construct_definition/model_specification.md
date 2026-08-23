# Model Specification

RSM-001 uses Fama-French 3-factor residualization.

Regression equation:

```text
excess_return_i,t =
    alpha_i
    + beta_mkt_i * MKT_RF_t
    + beta_smb_i * SMB_t
    + beta_hml_i * HML_t
    + residual_i,t
```

Regression type:

Ordinary Least Squares.

Regression window:

36 monthly observations.

Minimum observations:

24 monthly observations.

Return type:

Monthly excess returns.

The model specification is frozen and cannot be modified during IM, CV, MI, HV, PV or EV.
