from __future__ import annotations

from typing import Optional

import backtrader as bt

from engine.trade_journal import TradeJournalMixin
from strategies.stock_v131.detectors import SetupDetector, TrendDetector
from strategies.stock_v131.types import ManagedTradeState, SetupState, TrendDirection, TrendState


class TrendFlowingStockV131Strategy(TradeJournalMixin, bt.Strategy):
    """
    Research port of the MT5 v1.31 bot for stock-market testing.

    This version keeps the forex bot untouched and recreates the same pipeline
    in new Python files so we can observe how the idea behaves on stocks before
    designing stock-specific improvements.
    """

    params = (
        ("risk_per_trade", 0.01),
        ("price_step", 0.01),
        ("adx_period", 14),
        ("adx_threshold", 20.0),
        ("ema_period", 50),
        ("swing_lookback", 3),
        ("ob_lookback", 20),
        ("disp_multiplier", 1.5),
        ("disp_avg_bars", 5),
        ("fvg_max_bars", 16),
        ("sl_buffer_steps", 5),
        ("sl_atr_min_mult", 1.0),
        ("sl_atr_max_mult", 4.0),
        ("tp1_rr", 1.5),
        ("be_rr", 1.5),
        ("trailing_atr_mult", 2.0),
        ("max_open_trades", 1),
        ("max_daily_loss_pct", 3.0),
        ("max_drawdown_pct", 10.0),
    )

    def __init__(self) -> None:
        super().__init__()
        if len(self.datas) < 3:
            raise ValueError("TrendFlowingStockV131Strategy requires 15m, 1h, and 4h feeds.")

        self.data_ltf = self.datas[0]
        self.data_h1 = self.datas[1]
        self.data_h4 = self.datas[2]

        self.adx = bt.indicators.AverageDirectionalMovementIndex(self.data_h4, period=self.p.adx_period)
        self.di_plus = bt.indicators.PlusDI(self.data_h4, period=self.p.adx_period)
        self.di_minus = bt.indicators.MinusDI(self.data_h4, period=self.p.adx_period)
        self.ema = bt.indicators.ExponentialMovingAverage(self.data_h4.close, period=self.p.ema_period)
        self.atr_ltf = bt.indicators.AverageTrueRange(self.data_ltf, period=14)

        self.trend_detector = TrendDetector(
            data=self.data_h4,
            adx=self.adx,
            di_plus=self.di_plus,
            di_minus=self.di_minus,
            ema=self.ema,
            adx_threshold=self.p.adx_threshold,
            swing_lookback=self.p.swing_lookback,
        )
        self.setup_detector = SetupDetector(
            h1_data=self.data_h1,
            ltf_data=self.data_ltf,
            ob_lookback=self.p.ob_lookback,
            displacement_multiplier=self.p.disp_multiplier,
            displacement_avg_bars=self.p.disp_avg_bars,
            fvg_max_bars=self.p.fvg_max_bars,
        )

        self.trend_state = TrendState()
        self.setup_state = SetupState()
        self.trade_state = ManagedTradeState()
        self.last_h4_dt = None
        self.last_ltf_dt = None
        self.daily_start_value: Optional[float] = None
        self.current_day = None
        self.peak_value = 0.0
        self.buy_markers: list[tuple[object, float]] = []
        self.sell_markers: list[tuple[object, float]] = []

    def next(self) -> None:
        self._update_risk_guards()
        self._update_trend_state()
        self._update_setup_state()
        self._sync_pending_and_position_state()
        self._manage_open_position()
        self._place_new_entry_if_needed()

    def notify_order(self, order: bt.Order) -> None:
        super().notify_order(order)

        if order.status in (order.Submitted, order.Accepted):
            return

        if order.status == order.Completed:
            if self._orders_match(order, self.trade_state.entry_order):
                self.trade_state.entry_order = None
                self.trade_state.pending_bars = 0
                self.trade_state.position_direction = self.trade_state.order_direction
                self.trade_state.entry_price = float(order.executed.price)
                marker_dt = bt.num2date(order.executed.dt)
                self.buy_markers.append((marker_dt, float(order.executed.price)))
                self.trade_state.remaining_size = int(abs(order.executed.size))
                self.trade_state.initial_stop_price = self.trade_state.pending_stop_price
                self.trade_state.stop_price = self.trade_state.pending_stop_price
                self.trade_state.tp1_price = self.trade_state.pending_tp1_price
                self.update_trade_plan(
                    self._trade_key_from_order(order),
                    entry_price=self.trade_state.entry_price,
                    stop_loss=self.trade_state.stop_price,
                    take_profit=self.trade_state.tp1_price,
                    position_size=self.trade_state.remaining_size,
                )
                self._submit_protective_orders()
                return

            if self._orders_match(order, self.trade_state.tp1_order):
                self.trade_state.tp1_order = None
                marker_dt = bt.num2date(order.executed.dt)
                self.sell_markers.append((marker_dt, float(order.executed.price)))
                self.trade_state.tp1_hit = True
                self.trade_state.be_active = True
                self.trade_state.remaining_size = int(abs(self.position.size))
                self._cancel_order_if_active(self.trade_state.stop_order)
                self.trade_state.stop_order = None
                self.trade_state.stop_price = self._breakeven_stop_price()
                if self.trade_state.remaining_size > 0:
                    self._submit_stop_order(self.trade_state.remaining_size, self.trade_state.stop_price)
                return

            if self._orders_match(order, self.trade_state.stop_order):
                self.trade_state.stop_order = None
                marker_dt = bt.num2date(order.executed.dt)
                exit_price = float(order.executed.price) if order.executed.price else self.trade_state.stop_price
                self.sell_markers.append((marker_dt, exit_price))
                self._cancel_order_if_active(self.trade_state.tp1_order)
                self.trade_state.tp1_order = None
                if not self.position:
                    self._reset_trade_state(clear_setup=True)
                return

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._orders_match(order, self.trade_state.entry_order):
                self.trade_state.entry_order = None
            if self._orders_match(order, self.trade_state.stop_order):
                self.trade_state.stop_order = None
            if self._orders_match(order, self.trade_state.tp1_order):
                self.trade_state.tp1_order = None

    def _update_trend_state(self) -> None:
        current_h4_dt = self.data_h4.datetime.datetime(0)
        if current_h4_dt == self.last_h4_dt:
            return
        self.last_h4_dt = current_h4_dt
        previous_direction = self.trend_state.direction
        self.trend_state = self.trend_detector.evaluate(previous_direction=previous_direction)

    def _update_setup_state(self) -> None:
        current_ltf_dt = self.data_ltf.datetime.datetime(0)
        if current_ltf_dt == self.last_ltf_dt:
            return
        self.last_ltf_dt = current_ltf_dt
        self.setup_state = self.setup_detector.evaluate(
            trend_direction=self.trend_state.direction if self.trend_state.is_valid else TrendDirection.NONE,
            previous_state=self.setup_state,
        )
        if self.trade_state.entry_order:
            self.trade_state.pending_bars += 1
            if self.trade_state.pending_bars >= self.p.fvg_max_bars:
                self.cancel(self.trade_state.entry_order)
                self.trade_state.entry_order = None

    def _place_new_entry_if_needed(self) -> None:
        if not self.setup_state.setup_ready:
            return
        if self.trade_state.entry_order or self.position:
            return
        if self._risk_halted():
            return

        direction = self.setup_state.setup_direction
        entry_price = self.setup_state.fvg_mid
        stop_price = self._initial_stop_price(direction=direction, entry_price=entry_price)
        if stop_price is None:
            return

        size = self._calculate_size(reference_price=entry_price, stop_price=stop_price)
        if size <= 0:
            return

        tp1_price = self._tp1_price(direction=direction, entry_price=entry_price, stop_price=stop_price)
        self.trade_state.pending_entry_price = entry_price
        self.trade_state.pending_stop_price = stop_price
        self.trade_state.pending_tp1_price = tp1_price
        self.trade_state.pending_size = size
        self.trade_state.pending_bars = 0
        self.trade_state.order_direction = direction
        self.register_trade_plan(
            entry_price=entry_price,
            stop_loss=stop_price,
            take_profit=tp1_price,
            direction="LONG" if direction == TrendDirection.LONG else "SHORT",
            position_size=size,
        )

        if direction == TrendDirection.LONG:
            self.trade_state.entry_order = self.buy(price=entry_price, exectype=bt.Order.Limit, size=size)
        elif direction == TrendDirection.SHORT:
            self.trade_state.entry_order = self.sell(price=entry_price, exectype=bt.Order.Limit, size=size)

    def _submit_protective_orders(self) -> None:
        if self.trade_state.remaining_size <= 0:
            return

        half_size = max(self.trade_state.remaining_size // 2, 1)
        self._submit_stop_order(self.trade_state.remaining_size, self.trade_state.stop_price)

        if self.trade_state.position_direction == TrendDirection.LONG:
            self.trade_state.tp1_order = self.sell(
                exectype=bt.Order.Limit,
                price=self.trade_state.tp1_price,
                size=half_size,
            )
        elif self.trade_state.position_direction == TrendDirection.SHORT:
            self.trade_state.tp1_order = self.buy(
                exectype=bt.Order.Limit,
                price=self.trade_state.tp1_price,
                size=half_size,
            )

    def _submit_stop_order(self, size: int, stop_price: float) -> None:
        if size <= 0:
            return
        if self.trade_state.position_direction == TrendDirection.LONG:
            self.trade_state.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price, size=size)
        elif self.trade_state.position_direction == TrendDirection.SHORT:
            self.trade_state.stop_order = self.buy(exectype=bt.Order.Stop, price=stop_price, size=size)

    def _manage_open_position(self) -> None:
        if not self.position:
            return
        if not self.trade_state.tp1_hit:
            return

        new_stop = self._trailing_stop_price()
        if new_stop is None:
            return

        should_update = (
            self.trade_state.position_direction == TrendDirection.LONG and new_stop > self.trade_state.stop_price
        ) or (
            self.trade_state.position_direction == TrendDirection.SHORT and new_stop < self.trade_state.stop_price
        )
        if not should_update:
            return

        self._cancel_order_if_active(self.trade_state.stop_order)
        self.trade_state.stop_order = None
        self.trade_state.stop_price = new_stop
        self.trade_state.remaining_size = int(abs(self.position.size))
        self._submit_stop_order(self.trade_state.remaining_size, new_stop)

    def _sync_pending_and_position_state(self) -> None:
        if not self.position and not any(
            (
                self.trade_state.entry_order,
                self.trade_state.stop_order,
                self.trade_state.tp1_order,
            )
        ):
            if self.trade_state.position_direction != TrendDirection.NONE:
                self._reset_trade_state(clear_setup=True)

    def _calculate_size(self, reference_price: float, stop_price: float) -> int:
        risk_budget = self.broker.getvalue() * self.p.risk_per_trade
        risk_per_share = abs(reference_price - stop_price)
        if risk_budget <= 0 or risk_per_share <= 0:
            return 0
        raw_size = int(risk_budget / risk_per_share)
        affordable = int(self.broker.getcash() / max(reference_price, 0.01))
        return max(min(raw_size, affordable), 0)

    def _initial_stop_price(self, direction: TrendDirection, entry_price: float) -> float | None:
        if self.setup_state.sweep_price <= 0:
            return None
        buffer = self.p.sl_buffer_steps * self.p.price_step
        raw_stop = (
            self.setup_state.sweep_price - buffer
            if direction == TrendDirection.LONG
            else self.setup_state.sweep_price + buffer
        )
        atr_value = float(self.atr_ltf[0])
        if atr_value <= 0:
            return None
        sl_distance = abs(entry_price - raw_stop)
        sl_min = atr_value * self.p.sl_atr_min_mult
        sl_max = atr_value * self.p.sl_atr_max_mult

        if sl_distance < sl_min:
            raw_stop = entry_price - sl_min if direction == TrendDirection.LONG else entry_price + sl_min
        elif sl_distance > sl_max:
            raw_stop = entry_price - sl_max if direction == TrendDirection.LONG else entry_price + sl_max
        return round(raw_stop, 4)

    def _tp1_price(self, direction: TrendDirection, entry_price: float, stop_price: float) -> float:
        sl_distance = abs(entry_price - stop_price)
        target = entry_price + sl_distance * self.p.tp1_rr if direction == TrendDirection.LONG else entry_price - sl_distance * self.p.tp1_rr
        return round(target, 4)

    def _breakeven_stop_price(self) -> float:
        buffer = 2 * self.p.price_step
        return round(
            self.trade_state.entry_price + buffer
            if self.trade_state.position_direction == TrendDirection.LONG
            else self.trade_state.entry_price - buffer,
            4,
        )

    def _trailing_stop_price(self) -> float | None:
        atr_value = float(self.atr_ltf[0])
        if atr_value <= 0:
            return None
        distance = atr_value * self.p.trailing_atr_mult
        if self.trade_state.position_direction == TrendDirection.LONG:
            return round(float(self.data_ltf.close[0]) - distance, 4)
        if self.trade_state.position_direction == TrendDirection.SHORT:
            return round(float(self.data_ltf.close[0]) + distance, 4)
        return None

    def _update_risk_guards(self) -> None:
        current_dt = self.data_ltf.datetime.datetime(0)
        if self.current_day != current_dt.date():
            self.current_day = current_dt.date()
            self.daily_start_value = self.broker.getvalue()
        self.peak_value = max(self.peak_value, self.broker.getvalue())

    def _risk_halted(self) -> bool:
        portfolio_value = self.broker.getvalue()
        if self.daily_start_value:
            daily_pnl_pct = (portfolio_value - self.daily_start_value) / self.daily_start_value * 100.0
            if daily_pnl_pct <= -self.p.max_daily_loss_pct:
                return True
        if self.peak_value > 0:
            drawdown_pct = (self.peak_value - portfolio_value) / self.peak_value * 100.0
            if drawdown_pct >= self.p.max_drawdown_pct:
                return True
        return False

    def _cancel_order_if_active(self, order: object | None) -> None:
        if order and getattr(order, "status", None) not in (bt.Order.Canceled, bt.Order.Completed, bt.Order.Rejected):
            self.cancel(order)

    def _reset_trade_state(self, clear_setup: bool) -> None:
        self.trade_state = ManagedTradeState()
        if clear_setup:
            self.setup_state.setup_ready = False

    def notify_trade(self, trade: bt.Trade) -> None:
        super().notify_trade(trade)

    def _is_entry_completion(self, order: bt.Order) -> bool:
        return self._orders_match(order, self.trade_state.entry_order) and order.status == order.Completed

    def _is_exit_completion(self, order: bt.Order) -> bool:
        return self._orders_match(order, self.trade_state.stop_order) or self._orders_match(order, self.trade_state.tp1_order)

    def _is_pending_entry_order(self, order: bt.Order) -> bool:
        return self._orders_match(order, self.trade_state.entry_order)

    @staticmethod
    def _orders_match(left: object | None, right: object | None) -> bool:
        if left is None or right is None:
            return False
        return getattr(left, "ref", None) == getattr(right, "ref", None)
