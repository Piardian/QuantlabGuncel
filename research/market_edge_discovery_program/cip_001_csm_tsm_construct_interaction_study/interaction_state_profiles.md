# Interaction State Profiles

The interaction state matrix is saved as `interaction_matrix.csv`.

| interaction_state | observations | coverage | mean_csm_score | mean_tsm_direction_score | mean_future_return_21d | median_future_return_21d | positive_return_rate_21d | mean_future_return_63d | median_future_return_63d | positive_return_rate_63d | mean_future_return_126d | median_future_return_126d | positive_return_rate_126d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CSM_HIGH_x_TSM_HIGH | 178612 | 0.100977 | 0.950471 | 1 | 0.0197935 | 0.0165364 | 0.575762 | 0.0576793 | 0.0433023 | 0.605486 | 0.119726 | 0.0819334 | 0.63101 |
| CSM_NOT_HIGH_x_TSM_HIGH | 1099833 | 0.621782 | 0.56483 | 1 | 0.0117738 | 0.0129339 | 0.5828 | 0.0355897 | 0.0357189 | 0.622179 | 0.073419 | 0.0683705 | 0.651781 |
| CSM_NOT_HIGH_x_TSM_LOW | 490395 | 0.277241 | 0.190532 | -0.999741 | 0.018634 | 0.0166887 | 0.578519 | 0.0537099 | 0.0488854 | 0.619435 | 0.103716 | 0.0843895 | 0.639421 |

Supported by evidence:

- The dominant high-leadership region is CSM_HIGH x TSM_HIGH.
- CSM_NOT_HIGH x TSM_HIGH is materially larger than CSM_HIGH x TSM_HIGH.
- This supports a nested-state interpretation: cross-sectional leadership is a stricter state than positive own-trend.
