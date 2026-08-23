from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(equity_curve: pd.Series, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(equity_curve.index, equity_curve.values, color="#1f77b4", linewidth=1.8)
    ax.set_title("Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path


def plot_trade_chart(
    market_data: pd.DataFrame,
    buy_markers: list[tuple[object, float]],
    sell_markers: list[tuple[object, float]],
    output_path: Path,
    fast_period: int | None = None,
    slow_period: int | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chart_data = market_data.copy()
    close_prices = chart_data["Close"]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(chart_data.index, close_prices.values, color="#222222", linewidth=1.2, label="Close")

    if fast_period:
        ax.plot(
            chart_data.index,
            close_prices.rolling(fast_period).mean().values,
            color="#1f77b4",
            linewidth=1.1,
            label=f"SMA {fast_period}",
        )
    if slow_period:
        ax.plot(
            chart_data.index,
            close_prices.rolling(slow_period).mean().values,
            color="#ff7f0e",
            linewidth=1.1,
            label=f"SMA {slow_period}",
        )

    if buy_markers:
        buy_index, buy_prices = zip(*buy_markers)
        ax.scatter(buy_index, buy_prices, marker="^", s=80, color="#2ca02c", label="Buy", zorder=5)
    if sell_markers:
        sell_index, sell_prices = zip(*sell_markers)
        ax.scatter(sell_index, sell_prices, marker="v", s=80, color="#d62728", label="Sell", zorder=5)

    ax.set_title("Price Chart with Trade Markers")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path
