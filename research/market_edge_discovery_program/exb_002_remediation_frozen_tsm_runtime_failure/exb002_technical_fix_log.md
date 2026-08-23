# EXB-002 Technical Fix Log

## Modified File

```text
research/implementations/tsm_001/feature_pipeline.py
```

## Function

```text
TSM001FeaturePipeline.build_features
```

## Old Behavior

The implementation converted numeric direction scores to state labels using:

```text
DataFrame.replace({1.0: "POSITIVE", 0.0: "NEUTRAL", -1.0: "NEGATIVE"})
```

On the EXB-002 frozen input shape, this raised a Pandas runtime error.

## New Behavior

The implementation now initializes an object DataFrame and assigns the same labels using explicit masks:

```text
1.0  -> POSITIVE
0.0  -> NEUTRAL
-1.0 -> NEGATIVE
```

## Classification

FIX_CLASSIFICATION = TECHNICAL_ONLY

The fix changes state-label construction mechanics only. It does not change returns, sign logic, thresholds, lookbacks, eligibility, or temporal alignment.
