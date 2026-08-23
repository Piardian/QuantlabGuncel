from __future__ import annotations

import backtrader as bt

from strategies.base import BaseStrategy


class SmaCrossoverStrategy(BaseStrategy):
    """Simple long-only moving average crossover with managed exits."""

    params = (
        ("fast_period", 50),
        ("slow_period", 200),
    )

    def __init__(self) -> None:
        super().__init__()
        self.fast_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast_period)
        self.slow_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def should_enter_long(self) -> bool:
        return self.crossover[0] > 0

    def should_exit_long(self) -> bool:
        return self.crossover[0] < 0
