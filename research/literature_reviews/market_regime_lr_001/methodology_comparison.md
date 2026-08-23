# Methodology Comparison

## Markov-Switching / Hidden Markov Models

**Support level:** Strongly supported  
**Use:** Dominant academic tool for latent regime inference  
**Strengths:** Flexible, probabilistic, well-suited to persistent states  
**Limitations:** Can be hard to identify, sensitive to specification, and prone to lag near turning points

## Threshold Models / TAR / STAR

**Support level:** Moderately supported  
**Use:** Popular for nonlinear transitions and state-dependent dynamics  
**Strengths:** Intuitive, often easier to interpret than fully latent models  
**Limitations:** Threshold choice can be unstable and sample-dependent

## State-Space / Bayesian Regime-Switching

**Support level:** Strongly supported  
**Use:** Common in macro-finance and asset allocation settings  
**Strengths:** Handles latent state uncertainty directly  
**Limitations:** Estimation complexity and model risk

## Clustering / Unsupervised Classification

**Support level:** Moderate to limited  
**Use:** Often used in recent regime classification and practitioner work  
**Strengths:** Flexible and data-driven  
**Limitations:** Less standardized and sometimes difficult to interpret economically

## Rule-Based Classification

**Support level:** Strong for practitioner interpretability, limited for academic uniqueness  
**Use:** Bull/bear definitions, risk-on/risk-off heuristics, volatility thresholds  
**Strengths:** Transparent and easy to audit  
**Limitations:** Often ex post and less statistically rich than latent-state models

## Machine Learning

**Support level:** Limited to moderate  
**Use:** Growing practitioner interest and recent academic work  
**Strengths:** Can combine many observables  
**Limitations:** Higher risk of overfitting, and regime labels may be difficult to interpret

