from __future__ import annotations

import backtrader as bt

from engine.trade_journal import TradeJournalMixin, TradePlan


class RelativeStrengthPullbackV1Strategy(TradeJournalMixin, bt.Strategy):
    """Leader-stock pullback continuation research strategy."""

    params = (
        ("risk_per_trade", 0.01),
        ("ema_trend_period", 200),
        ("ema_pullback_period", 50),
        ("ema_signal_period", 20),
        ("atr_period", 14),
        ("relative_strength_lookback", 60),
        ("relative_strength_threshold", 0.05),
        ("initial_stop_atr_multiple", 1.5),
        ("trailing_stop_atr_multiple", 2.0),
        ("max_holding_bars", 40),
        ("max_positions", 3),
        ("consolidation_bars", 5),
        ("compression_threshold", 0.04),
        ("skip_relative_strength_filter", False),
        ("enable_ema200_filter", True),
        ("enable_ema200_slope", True),
        ("enable_relative_strength", True),
        ("enable_ema50_filter", True),
        ("enable_pullback_filter", True),
    )

    def __init__(self) -> None:
        super().__init__()
        if len(self.datas) < 2:
            raise ValueError("relative_strength_pullback_v1 requires stock and benchmark feeds.")

        self.data_stock = self.datas[0]
        self.data_benchmark = self.datas[1]

        self.ema200 = bt.indicators.ExponentialMovingAverage(self.data_stock.close, period=self.p.ema_trend_period)
        self.ema50 = bt.indicators.ExponentialMovingAverage(self.data_stock.close, period=self.p.ema_pullback_period)
        self.ema20 = bt.indicators.ExponentialMovingAverage(self.data_stock.close, period=self.p.ema_signal_period)
        self.atr = bt.indicators.AverageTrueRange(self.data_stock, period=self.p.atr_period)

        self.next_trade_id = 1
        self.pending_entries: dict[int, bt.Order] = {}
        self.exit_orders: dict[int, bt.Order] = {}
        self.active_sizes: dict[int, int] = {}
        self.planned_stops: dict[int, float] = {}
        self.entry_bars: dict[int, int] = {}
        self.initial_stops: dict[int, float] = {}
        self.current_stops: dict[int, float] = {}
        self.pending_exit_reasons: dict[int, str] = {}
        self.buy_markers: list[tuple[object, float]] = []
        self.sell_markers: list[tuple[object, float]] = []

    def next(self) -> None:
        self._manage_open_trades()

        if self._active_trade_count() >= self.p.max_positions:
            return
        if not self._should_enter_long():
            return

        reference_price = float(self.data_stock.close[0])
        stop_price = self._consolidation_low()
        if stop_price <= 0 or reference_price <= stop_price:
            return

        size = self.calculate_position_size(reference_price=reference_price, stop_price=stop_price)
        if size <= 0:
            return

        trade_id = self.next_trade_id
        self.next_trade_id += 1
        self.register_trade_plan(
            entry_price=reference_price,
            stop_loss=stop_price,
            take_profit=float(self.ema20[0]),
            direction="LONG",
            position_size=size,
            plan_key=trade_id,
        )
        self.planned_stops[trade_id] = stop_price
        self.pending_entries[trade_id] = self.buy(size=size, tradeid=trade_id)

    def notify_order(self, order: bt.Order) -> None:
        super().notify_order(order)

        if order.status in (order.Submitted, order.Accepted):
            return

        trade_id = self._trade_key_from_order(order)

        if order.status == order.Completed:
            if self._orders_match(order, self.pending_entries.get(trade_id)) and order.isbuy():
                entry_price = float(order.executed.price)
                size = int(abs(order.executed.size))
                initial_stop = self.planned_stops.get(trade_id, self._consolidation_low())
                if size <= 0 or initial_stop <= 0:
                    self.pending_entries.pop(trade_id, None)
                    self.planned_stops.pop(trade_id, None)
                    return

                self.buy_markers.append((bt.num2date(order.executed.dt), entry_price))
                self.pending_entries.pop(trade_id, None)
                self.planned_stops.pop(trade_id, None)
                self.active_sizes[trade_id] = size
                self.entry_bars[trade_id] = len(self)
                self.initial_stops[trade_id] = initial_stop
                self.current_stops[trade_id] = initial_stop
                self.update_trade_plan(
                    trade_id,
                    entry_price=entry_price,
                    stop_loss=initial_stop,
                    take_profit=float(self.ema20[0]),
                    position_size=size,
                )
                return

            if self._orders_match(order, self.exit_orders.get(trade_id)):
                self.sell_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                self.exit_orders.pop(trade_id, None)
                return

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._orders_match(order, self.pending_entries.get(trade_id)):
                self.pending_entries.pop(trade_id, None)
                self.planned_stops.pop(trade_id, None)
            if self._orders_match(order, self.exit_orders.get(trade_id)):
                self.exit_orders.pop(trade_id, None)
                self.pending_exit_reasons.pop(trade_id, None)

    def notify_trade(self, trade: bt.Trade) -> None:
        super().notify_trade(trade)
        if trade.isclosed:
            trade_id = self._trade_key_from_trade(trade)
            self.active_sizes.pop(trade_id, None)
            self.planned_stops.pop(trade_id, None)
            self.entry_bars.pop(trade_id, None)
            self.initial_stops.pop(trade_id, None)
            self.current_stops.pop(trade_id, None)
            self.exit_orders.pop(trade_id, None)
            self.pending_exit_reasons.pop(trade_id, None)

    def calculate_position_size(self, reference_price: float, stop_price: float) -> int:
        risk_budget = self.broker.getvalue() * self.p.risk_per_trade
        risk_per_share = max(reference_price - stop_price, 0.0)
        if risk_budget <= 0 or risk_per_share <= 0:
            return 0

        raw_size = int(risk_budget / risk_per_share)
        if raw_size <= 0:
            return 0

        affordable_size = int(self.broker.getcash() / max(reference_price, 0.01))
        return max(min(raw_size, affordable_size), 0)

    def _manage_open_trades(self) -> None:
        if not self.active_sizes:
            return

        current_close = float(self.data_stock.close[0])
        current_atr = float(self.atr[0])
        ema20_level = float(self.ema20[0])
        current_low = float(self.data_stock.low[0])
        if current_atr <= 0:
            return

        for trade_id, size in list(self.active_sizes.items()):
            if size <= 0:
                continue

            if trade_id in self.exit_orders:
                continue

            trailing_stop = current_close - (current_atr * self.p.trailing_stop_atr_multiple)
            if trailing_stop > self.current_stops.get(trade_id, 0.0):
                self.current_stops[trade_id] = trailing_stop

            exit_reason = None
            current_stop = self.current_stops.get(trade_id, 0.0)
            initial_stop = self.initial_stops.get(trade_id, current_stop)

            if current_low <= current_stop:
                exit_reason = "ATR_TRAIL" if current_stop > initial_stop + 1e-8 else "STOP"
            elif current_close < ema20_level:
                exit_reason = "EMA_EXIT"
            elif len(self) - self.entry_bars.get(trade_id, len(self)) >= self.p.max_holding_bars:
                exit_reason = "TIME_EXIT"

            if exit_reason is None:
                continue

            self.pending_exit_reasons[trade_id] = exit_reason
            self.exit_orders[trade_id] = self.sell(size=size, tradeid=trade_id)

    def _should_enter_long(self) -> bool:
        required_bars = max(
            self.p.ema_trend_period + 1,
            self.p.ema_pullback_period,
            self.p.ema_signal_period,
            self.p.atr_period,
            self.p.relative_strength_lookback + 1,
            self.p.consolidation_bars + 1,
        )
        if len(self) < required_bars or len(self.data_benchmark) < self.p.relative_strength_lookback + 1:
            return False

        close_price = float(self.data_stock.close[0])
        ema200 = float(self.ema200[0])
        ema200_prev = float(self.ema200[-1])
        ema50 = float(self.ema50[0])
        atr_value = float(self.atr[0])
        if atr_value <= 0:
            return False

        if self.p.enable_ema200_filter and close_price <= ema200:
            return False
        if self.p.enable_ema200_slope and ema200 <= ema200_prev:
            return False

        if self.p.enable_relative_strength and not self.p.skip_relative_strength_filter:
            stock_return_60 = (close_price / float(self.data_stock.close[-self.p.relative_strength_lookback])) - 1.0
            benchmark_return_60 = (
                float(self.data_benchmark.close[0]) / float(self.data_benchmark.close[-self.p.relative_strength_lookback])
            ) - 1.0
            relative_strength = stock_return_60 - benchmark_return_60
            if relative_strength <= self.p.relative_strength_threshold:
                return False

        if self.p.enable_ema50_filter and close_price <= ema50:
            return False

        if self.p.enable_pullback_filter and not self._has_valid_consolidation_breakout(close_price):
            return False

        return True

    def _has_valid_consolidation_breakout(self, close_price: float) -> bool:
        highest_high = self._consolidation_high()
        lowest_low = self._consolidation_low()
        highest_close = max(float(self.data_stock.close[-bar]) for bar in range(1, self.p.consolidation_bars + 1))

        if lowest_low <= 0:
            return False
        range_pct = (highest_high - lowest_low) / lowest_low
        if range_pct > self.p.compression_threshold:
            return False
        if float(self.ema50[0]) <= float(self.ema200[0]):
            return False
        return close_price > highest_close

    def _consolidation_high(self) -> float:
        return max(float(self.data_stock.high[-bar]) for bar in range(1, self.p.consolidation_bars + 1))

    def _consolidation_low(self) -> float:
        return min(float(self.data_stock.low[-bar]) for bar in range(1, self.p.consolidation_bars + 1))

    def _classify_exit_reason(self, exit_price: float, plan: TradePlan) -> str:
        if self._journal_last_exit_kind == "MARKET":
            return self.pending_exit_reasons.get(self._journal_current_trade_key, "UNKNOWN")

        return super()._classify_exit_reason(exit_price=exit_price, plan=plan)

    def _is_entry_completion(self, order: bt.Order) -> bool:
        trade_id = self._trade_key_from_order(order)
        return self._orders_match(order, self.pending_entries.get(trade_id)) and order.status == order.Completed

    def _is_exit_completion(self, order: bt.Order) -> bool:
        trade_id = self._trade_key_from_order(order)
        return self._orders_match(order, self.exit_orders.get(trade_id))

    def _is_pending_entry_order(self, order: bt.Order) -> bool:
        trade_id = self._trade_key_from_order(order)
        return self._orders_match(order, self.pending_entries.get(trade_id))

    @staticmethod
    def _orders_match(left: bt.Order | None, right: bt.Order | None) -> bool:
        if left is None or right is None:
            return False
        return getattr(left, "ref", None) == getattr(right, "ref", None)

    def _cancel_order_if_active(self, order: bt.Order | None) -> None:
        if order and order.status not in (bt.Order.Canceled, bt.Order.Completed, bt.Order.Rejected):
            self.cancel(order)

    def _active_trade_count(self) -> int:
        return len(self.active_sizes) + len(self.pending_entries)
