# Methodology Comparison

## Purpose

This file compares common Credit Stress measurement methodologies. It does not select the official CRD-001 definition.

| Methodology | Strengths | Limitations | Reproducibility |
|---|---|---|---|
| Treasury-Relative Corporate Spread | Simple, transparent, long history for some series. | Mixes default risk, liquidity, duration, and risk premia. | High |
| Option-Adjusted Spread | Adjusts for embedded options and spread-to-curve conventions. | Vendor methodology may be less transparent. | Medium to high if public series exists |
| High-Yield OAS | Sensitive to stress and risk appetite. | Shorter history and composition changes. | High for public FRED series |
| Investment-Grade OAS | Captures higher-quality corporate stress. | May react less sharply to extreme risk stress. | High for public series |
| Baa-Treasury Spread | Long historical availability. | Broad proxy; not a pure credit mechanism. | High |
| Baa-Aaa Spread | Focuses on credit-quality gradient. | Narrower credit-quality interpretation. | High |
| CDS-Based Measures | Directly tied to credit protection markets. | Data access, contract conventions, and liquidity issues. | Variable |
| Excess Bond Premium | Attempts to isolate non-default credit premium. | Model-dependent and harder to reproduce without full methodology/data. | Medium |
| Financial Stress Index Credit Components | Contextualizes credit inside broader stress. | May mix constructs if used as standalone credit stress. | Medium |

## Methodological Caution

The same term "credit stress" can mean different things depending on the chosen proxy. CD-001 must prioritize conceptual clarity and reproducibility over expected performance.

