# Construct Limitations

## Measurement Limitations

- LIQ-001 captures a daily price-impact/illiquidity proxy, not the full multidimensional liquidity construct.
- Bid-ask spread, order-book depth, immediacy, and resiliency are excluded.
- Daily data can miss intraday liquidity breakdowns.
- Dollar volume can be high during stress, so volume alone does not guarantee true liquidity.
- Corporate actions, bad volume data, and ticker history issues can affect the security-level proxy.

## Universe Limitations

- A current-constituent universe may introduce survivorship bias.
- A small universe may underrepresent aggregate liquidity.
- A changing historical universe would be better but may not be available.

## Model Limitations

- The 20-day smoothing window and 252-day normalization window are fixed for reproducibility, not optimized.
- The construct is continuous and does not define liquidity regimes at CD-001.
- No threshold is selected.

## Interpretation Limitations

- LIQ-001 should be interpreted as aggregate daily illiquidity stress.
- It should not be interpreted as an exact execution-cost estimate.
- It should not be treated as predictive or economically useful until later stages evaluate those questions.

