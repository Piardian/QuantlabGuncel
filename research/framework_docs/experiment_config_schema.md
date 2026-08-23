# Experiment Config Schema

```json
{
  "experiment_id": "ablate_breakout_v1",
  "description": "Remove only breakout confirmation.",
  "strategy_version": "leadership_expansion_v1",
  "version": "1",
  "research_notes": "Controlled ablation.",
  "component_overrides": {"enable_breakout_confirmation": false},
  "expected_baseline": false,
  "random_seed": null
}
```

Only component names present in the registry are accepted.
