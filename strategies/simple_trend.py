from __future__ import annotations

import backtrader as bt

from strategies.base import BaseStrategy


class SimpleTrendStrategy(BaseStrategy):
    """Long-only EMA pullback trend strategy for baseline edge validation."""

    params = (
        ("ema_period", 50),
        ("atr_period", 14),
        ("pullback_atr_threshold", 0.5),
        ("shallow_pullback_pct", 0.01),
        ("swing_lookback", 10),
        ("reward_risk_ratio", 2.0),
    )

    def __init__(self) -> None:
        super().__init__()
        self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.p.ema_period)
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.p.atr_period)
        self.swing_low = bt.indicators.Lowest(self.data.low, period=self.p.swing_lookback)
        self.planned_stop_price: float | None = None

    def should_enter_long(self) -> bool:
        if len(self) < max(self.p.ema_period, self.p.atr_period) + self.p.swing_lookback:
            return False

        current_open = float(self.data.open[0])
        current_close = float(self.data.close[0])
        current_low = float(self.data.low[0])
        current_ema = float(self.ema[0])
        current_atr = float(self.atr[0])
        recent_high = max(float(self.data.high[-bar]) for bar in range(1, self.p.swing_lookback + 1))

        if current_atr <= 0 or recent_high <= 0:
            return False
        if current_close <= current_ema:
            return False
        if current_close <= current_open:
            return False

        ema_touch = current_low <= current_ema
        ema_proximity = abs(current_close - current_ema) <= current_atr * self.p.pullback_atr_threshold
        shallow_retracement = (recent_high - current_close) / recent_high >= self.p.shallow_pullback_pct

        return ema_touch or ema_proximity or shallow_retracement

    def should_exit_long(self) -> bool:
        if len(self) < self.p.ema_period:
            return False
        return float(self.data.close[0]) < float(self.ema[0])

    def get_long_stop_price(self) -> float:
        self.planned_stop_price = float(self.swing_low[0])
        return self.planned_stop_price

    def get_long_take_profit_price(self, entry_price: float) -> float:
        stop_price = self.get_long_stop_price()
        risk_per_share = entry_price - stop_price
        if risk_per_share <= 0:
            return entry_price
        return entry_price + (risk_per_share * self.p.reward_risk_ratio)

    def _submit_exit_orders(self, entry_price: float, size: float) -> None:
        stop_price = self.planned_stop_price if self.planned_stop_price is not None else self.get_long_stop_price()
        risk_per_share = entry_price - stop_price
        if risk_per_share <= 0:
            self._clear_exit_orders()
            self.planned_stop_price = None
            return

        take_profit_price = entry_price + (risk_per_share * self.p.reward_risk_ratio)
        self.stop_order = self.sell(
            exectype=bt.Order.Stop,
            price=stop_price,
            size=size,
        )
        self.take_profit_order = self.sell(
            exectype=bt.Order.Limit,
            price=take_profit_price,
            size=size,
        )
        self.planned_stop_price = None
