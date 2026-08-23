from __future__ import annotations

import backtrader as bt

from engine.trade_journal import TradeJournalMixin, TradePlan


class MeanReversionV1Strategy(TradeJournalMixin, bt.Strategy):
    """Long-only equity mean reversion with a long-term trend filter."""

    params = (
        ("risk_per_trade", 0.01),
        ("ema_trend_period", 200),
        ("ema_exit_period", 20),
        ("rsi_period", 2),
        ("rsi_threshold", 10.0),
        ("bb_period", 20),
        ("bb_devfactor", 2.0),
        ("atr_period", 14),
        ("ema20_distance_atr", 1.0),
        ("stop_atr_multiple", 1.5),
        ("max_positions", 3),
    )

    def __init__(self) -> None:
        super().__init__()
        self.ema200 = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.p.ema_trend_period)
        self.ema20 = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.p.ema_exit_period)
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.p.atr_period)
        self.rsi2 = bt.indicators.RSI_Safe(self.data.close, period=self.p.rsi_period)
        self.bbands = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.bb_period,
            devfactor=self.p.bb_devfactor,
        )

        self.next_trade_id = 1
        self.pending_entries: dict[int, bt.Order] = {}
        self.stop_orders: dict[int, bt.Order] = {}
        self.exit_orders: dict[int, bt.Order] = {}
        self.active_sizes: dict[int, int] = {}
        self.risk_distances: dict[int, float] = {}
        self.target_levels: dict[int, float] = {}
        self.pending_exit_reasons: dict[int, str] = {}
        self.buy_markers: list[tuple[object, float]] = []
        self.sell_markers: list[tuple[object, float]] = []

    def next(self) -> None:
        self._manage_open_trades()

        if self._active_trade_count() >= self.p.max_positions:
            return
        if not self._should_enter_long():
            return

        reference_price = float(self.data.close[0])
        atr_value = float(self.atr[0])
        risk_distance = atr_value * self.p.stop_atr_multiple
        stop_price = reference_price - risk_distance
        if risk_distance <= 0 or stop_price <= 0:
            return

        size = self.calculate_position_size(reference_price=reference_price, stop_price=stop_price)
        if size <= 0:
            return

        trade_id = self.next_trade_id
        self.next_trade_id += 1
        self.risk_distances[trade_id] = risk_distance
        self.target_levels[trade_id] = self._entry_target_level(reference_price)
        self.register_trade_plan(
            entry_price=reference_price,
            stop_loss=stop_price,
            take_profit=self.target_levels[trade_id],
            direction="LONG",
            position_size=size,
            plan_key=trade_id,
        )
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
                stop_price = entry_price - self.risk_distances.get(trade_id, 0.0)
                if stop_price <= 0 or size <= 0:
                    self.pending_entries.pop(trade_id, None)
                    return

                self.buy_markers.append((bt.num2date(order.executed.dt), entry_price))
                self.pending_entries.pop(trade_id, None)
                self.active_sizes[trade_id] = size
                self.update_trade_plan(
                    trade_id,
                    entry_price=entry_price,
                    stop_loss=stop_price,
                    take_profit=self.target_levels.get(trade_id, entry_price),
                    position_size=size,
                )
                self.stop_orders[trade_id] = self.sell(
                    exectype=bt.Order.Stop,
                    price=stop_price,
                    size=size,
                    tradeid=trade_id,
                )
                return

            if self._orders_match(order, self.stop_orders.get(trade_id)):
                self.sell_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                self.stop_orders.pop(trade_id, None)
                sibling = self.exit_orders.pop(trade_id, None)
                self._cancel_order_if_active(sibling)
                return

            if self._orders_match(order, self.exit_orders.get(trade_id)):
                self.sell_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                self.exit_orders.pop(trade_id, None)
                sibling = self.stop_orders.pop(trade_id, None)
                self._cancel_order_if_active(sibling)
                return

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._orders_match(order, self.pending_entries.get(trade_id)):
                self.pending_entries.pop(trade_id, None)
                self.risk_distances.pop(trade_id, None)
                self.target_levels.pop(trade_id, None)
            if self._orders_match(order, self.stop_orders.get(trade_id)):
                self.stop_orders.pop(trade_id, None)
            if self._orders_match(order, self.exit_orders.get(trade_id)):
                self.exit_orders.pop(trade_id, None)
                self.pending_exit_reasons.pop(trade_id, None)

    def notify_trade(self, trade: bt.Trade) -> None:
        super().notify_trade(trade)
        if trade.isclosed:
            trade_id = self._trade_key_from_trade(trade)
            self.active_sizes.pop(trade_id, None)
            self.stop_orders.pop(trade_id, None)
            self.exit_orders.pop(trade_id, None)
            self.risk_distances.pop(trade_id, None)
            self.target_levels.pop(trade_id, None)
            self.pending_exit_reasons.pop(trade_id, None)

    def calculate_position_size(self, reference_price: float, stop_price: float) -> int:
        risk_budget = self.broker.getvalue() * self.p.risk_per_trade
        risk_per_share = max(reference_price - stop_price, 0.0)
        if risk_budget <= 0 or risk_per_share <= 0:
            return 0

        raw_size = int(risk_budget / risk_per_share)
        if raw_size <= 0:
            return 0

        available_cash = self.broker.getcash()
        affordable_size = int(available_cash / max(reference_price, 0.01))
        return max(min(raw_size, affordable_size), 0)

    def _manage_open_trades(self) -> None:
        if not self.active_sizes:
            return

        current_close = float(self.data.close[0])
        ema_level = float(self.ema20[0])
        bb_mid = float(self.bbands.mid[0])

        exit_reason = None
        if current_close >= ema_level:
            exit_reason = "EMA_EXIT"
        elif current_close >= bb_mid:
            exit_reason = "BB_EXIT"

        if exit_reason is None:
            return

        for trade_id, size in list(self.active_sizes.items()):
            if trade_id in self.exit_orders:
                continue
            self.pending_exit_reasons[trade_id] = exit_reason
            sibling = self.stop_orders.pop(trade_id, None)
            self._cancel_order_if_active(sibling)
            self.exit_orders[trade_id] = self.sell(size=size, tradeid=trade_id)

    def _should_enter_long(self) -> bool:
        required_bars = max(self.p.ema_trend_period, self.p.ema_exit_period, self.p.bb_period, self.p.atr_period)
        if len(self) < required_bars:
            return False

        close_price = float(self.data.close[0])
        ema200 = float(self.ema200[0])
        ema20 = float(self.ema20[0])
        atr_value = float(self.atr[0])
        rsi_value = float(self.rsi2[0])
        lower_band = float(self.bbands.bot[0])

        if atr_value <= 0:
            return False
        if close_price <= ema200:
            return False
        if rsi_value >= self.p.rsi_threshold:
            return False
        if close_price >= lower_band:
            return False
        if (ema20 - close_price) < (atr_value * self.p.ema20_distance_atr):
            return False
        return True

    def _entry_target_level(self, reference_price: float) -> float:
        targets = [float(self.ema20[0]), float(self.bbands.mid[0])]
        targets_above_entry = [target for target in targets if target >= reference_price]
        if targets_above_entry:
            return min(targets_above_entry)
        return max(targets)

    def _classify_exit_reason(self, exit_price: float, plan: TradePlan) -> str:
        if self._journal_last_exit_kind == "STOP":
            return "STOP"
        if self._journal_last_exit_kind == "MARKET":
            return self.pending_exit_reasons.get(self._journal_current_trade_key, "EMA_EXIT")
        return super()._classify_exit_reason(exit_price=exit_price, plan=plan)

    def _is_entry_completion(self, order: bt.Order) -> bool:
        trade_id = self._trade_key_from_order(order)
        return self._orders_match(order, self.pending_entries.get(trade_id)) and order.status == order.Completed

    def _is_exit_completion(self, order: bt.Order) -> bool:
        trade_id = self._trade_key_from_order(order)
        return self._orders_match(order, self.stop_orders.get(trade_id)) or self._orders_match(order, self.exit_orders.get(trade_id))

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
