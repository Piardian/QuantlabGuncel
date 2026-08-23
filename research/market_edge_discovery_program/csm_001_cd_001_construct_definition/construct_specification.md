# Construct Specification

## Construct ID

`CSM-001`

## Construct Name

Canonical 12-1 Cross-Sectional Momentum State

## Mathematical Specification

For each security `i` and date `t`:

```text
P_i,t       = adjusted_close_i,t
P_i,t-21    = adjusted_close_i,t-21
P_i,t-252   = adjusted_close_i,t-252
R12_1_i,t   = P_i,t-21 / P_i,t-252 - 1
```

For each valid date `t`, rank all eligible `R12_1_i,t` values cross-sectionally.

```text
rank_i,t = average_rank(R12_1_i,t, ascending=True)
score_i,t = (rank_i,t - 1) / (N_t - 1)
top_decile_i,t = score_i,t >= 0.90
```

Where `N_t` is the number of eligible securities on date `t`.

## Validity Conditions

```text
P_i,t > 0
P_i,t-21 > 0
P_i,t-252 > 0
R12_1_i,t is finite
N_t >= 50
```

## Output Semantics

`score_i,t = 0.00` means the weakest relative prior performer among eligible securities on date `t`.

`score_i,t = 1.00` means the strongest relative prior performer among eligible securities on date `t`.

`top_decile_i,t = True` means the security belongs to the highest prior-return tail under the frozen threshold.

## Determinism Requirements

- Input dates must be sorted ascending.
- Tickers must be sorted deterministically.
- Duplicate dates must not create multiple observations.
- Non-positive prices must be treated as missing.
- Ties must use average-rank behavior.
- No random process is permitted.
