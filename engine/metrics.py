from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(slots=True)
class BacktestMetrics:
    total_return_pct: float
    net_profit: float
    win_rate_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float | None
    total_trades: int
    avg_r: float | None
    expectancy: float | None


def build_metrics(
    initial_capital: float,
    final_value: float,
    trade_analysis: dict[str, Any],
    drawdown_analysis: dict[str, Any],
    sharpe_analysis: dict[str, Any],
    trades_dataframe: pd.DataFrame | None = None,
) -> BacktestMetrics:
    total_closed = int(trade_analysis.get("total", {}).get("closed", 0) or 0)
    won_total = int(trade_analysis.get("won", {}).get("total", 0) or 0)
    win_rate = (won_total / total_closed * 100.0) if total_closed else 0.0

    drawdown_value = drawdown_analysis.get("max", {}).get("drawdown", 0.0) or 0.0
    sharpe_ratio = sharpe_analysis.get("sharperatio")
    sharpe_ratio = float(sharpe_ratio) if sharpe_ratio is not None else None
    avg_r = None
    expectancy = None

    if trades_dataframe is not None and not trades_dataframe.empty:
        if "R_multiple" in trades_dataframe.columns:
            r_values = pd.to_numeric(trades_dataframe["R_multiple"], errors="coerce").dropna()
            if not r_values.empty:
                avg_r = float(r_values.mean())
                expectancy = avg_r

    return BacktestMetrics(
        total_return_pct=((final_value / initial_capital) - 1.0) * 100.0,
        net_profit=final_value - initial_capital,
        win_rate_pct=win_rate,
        max_drawdown_pct=float(drawdown_value),
        sharpe_ratio=sharpe_ratio,
        total_trades=total_closed,
        avg_r=avg_r,
        expectancy=expectancy,
    )
