# CPP-001 Data Quality Limitations

- CPP-001 uses exact-date intersection of frozen serialized outputs; it does not resample, forward-fill, or impute any construct series.
- MR-001 does not expose a named stress_probability column; CPP-001 records posterior_state_0 as the numeric alignment column because the serialized output labels state 0 as STRESS. This is an inventory mapping, not a construct modification.
- Most constructs expose both raw/core and normalized state outputs. CPP-001 records both and uses frozen normalized outputs for alignment where available; raw/core outputs remain documented.
- CRD-001 begins materially later than most constructs in the current serialized output, which determines the all-construct common sample start date.
- Quality flags differ by construct. Some outputs expose explicit flags; others expose coverage/valid-observation diagnostics instead.
- No statistical relationship analysis is performed in CPP-001.
