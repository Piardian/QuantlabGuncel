# Liquidity and Capacity Registry

WER-002 must evaluate liquidity and capacity using predefined proxy rules.

## Required Liquidity Proxies

If volume data are available:

- Average dollar volume
- Minimum dollar volume
- Dollar-volume coverage
- Fraction of selected names passing liquidity thresholds

If volume data are unavailable:

WER-002 must explicitly report:

**Liquidity capacity analysis limited by unavailable volume data**

## Predefined Liquidity Thresholds

| Threshold | Average dollar volume |
|---|---:|
| Loose | $10 million |
| Moderate | $50 million |
| Strict | $100 million |

## Capacity Proxy

Assume a hypothetical account size grid:

- $100,000
- $1,000,000
- $10,000,000

For each account size, estimate whether equal-weight position sizing would exceed:

- 1% of average daily dollar volume
- 5% of average daily dollar volume

These are feasibility proxies only.
