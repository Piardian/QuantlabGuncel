# RSM-001 / IM-001 Implementation Development & Verification

Purpose: implement the frozen RSM-001 Fama-French 3-Factor Standardized 12-1 Residual Momentum Rank.

Required:

- Monthly adjusted security returns.
- Monthly Fama-French 3-factor returns.
- Monthly risk-free rate.
- Rolling 36-month OLS residualization.
- 12-1 residual aggregation.
- Residual volatility standardization.
- Cross-sectional ranking.

If factor data is unavailable, IM-001 must either obtain it from a documented public source or conclude implementation incomplete.

Forbidden:

- Changing factor model.
- Changing regression window.
- Changing formation window.
- Backtesting.
- Alpha claims.
- Parameter optimization.
