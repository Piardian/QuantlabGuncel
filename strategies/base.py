from __future__ import annotations

from typing import Optional

import backtrader as bt

from engine.trade_journal import TradeJournalMixin


class BaseStrategy(TradeJournalMixin, bt.Strategy):
    """
    Base class with bracket-exit handling and risk-based position sizing.

    Orders are submitted only from information available on the current bar and
    filled by Backtrader on subsequent bars, which keeps the system free of
    lookahead bias.
    """

    params = (
        ("risk_per_trade", 0.01),
        ("stop_loss_pct", 0.05),
        ("take_profit_pct", 0.1),
        ("allow_short", False),
    )

    def __init__(self) -> None:
        super().__init__()
        self.entry_order: Optional[bt.Order] = None
        self.stop_order: Optional[bt.Order] = None
        self.take_profit_order: Optional[bt.Order] = None
        self.last_entry_price: Optional[float] = None
        self.buy_markers: list[tuple[object, float]] = []
        self.sell_markers: list[tuple[object, float]] = []

    def next(self) -> None:
        if self.entry_order:
            return

        if not self.position and self.should_enter_long():
            stop_price = self.get_long_stop_price()
            size = self.calculate_position_size(reference_price=float(self.data.close[0]), stop_price=stop_price)
            if size > 0:
                self.register_trade_plan(
                    entry_price=float(self.data.close[0]),
                    stop_loss=stop_price,
                    take_profit=self.get_long_take_profit_price(entry_price=float(self.data.close[0])),
                    direction="LONG",
                    position_size=size,
                )
                self.entry_order = self.buy(size=size)
            return

        if self.position and self.should_exit_long():
            self.close_position()

    def notify_order(self, order: bt.Order) -> None:
        super().notify_order(order)

        if order.status in (order.Submitted, order.Accepted):
            return

        if order.status == order.Completed:
            if self._orders_match(order, self.entry_order) and order.isbuy():
                self.last_entry_price = float(order.executed.price)
                self.buy_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                stop_price = self.last_entry_price * (1.0 - self.p.stop_loss_pct)
                take_profit_price = self.get_long_take_profit_price(entry_price=self.last_entry_price)
                self.update_trade_plan(
                    self._trade_key_from_order(order),
                    entry_price=self.last_entry_price,
                    stop_loss=stop_price,
                    take_profit=take_profit_price,
                    position_size=abs(order.executed.size),
                )
                self._submit_exit_orders(entry_price=self.last_entry_price, size=abs(order.executed.size))
                self.entry_order = None
                return

            if self._orders_match(order, self.stop_order) or self._orders_match(order, self.take_profit_order):
                self.sell_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                sibling = self.take_profit_order if self._orders_match(order, self.stop_order) else self.stop_order
                self._cancel_order_if_active(sibling)
                self._clear_exit_orders()
                return

            if order.issell() and not self.position:
                self.sell_markers.append((bt.num2date(order.executed.dt), float(order.executed.price)))
                self.entry_order = None
                self._clear_exit_orders()
                return

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._orders_match(order, self.entry_order):
                self.entry_order = None
            if self._orders_match(order, self.stop_order) or self._orders_match(order, self.take_profit_order):
                self._clear_exit_orders()

    def notify_trade(self, trade: bt.Trade) -> None:
        super().notify_trade(trade)
        if trade.isclosed:
            self.last_entry_price = None

    def calculate_position_size(self, reference_price: float, stop_price: float) -> int:
        risk_budget = self.broker.getvalue() * self.p.risk_per_trade
        risk_per_share = max(reference_price - stop_price, 0.0)
        if risk_budget <= 0 or risk_per_share <= 0:
            return 0

        raw_size = int(risk_budget / risk_per_share)
        if raw_size <= 0:
            return 0

        available_cash = self.broker.getcash()
        affordable_size = int(available_cash / reference_price)
        return max(min(raw_size, affordable_size), 0)

    def get_long_stop_price(self) -> float:
        return float(self.data.close[0]) * (1.0 - self.p.stop_loss_pct)

    def get_long_take_profit_price(self, entry_price: float) -> float:
        return entry_price * (1.0 + self.p.take_profit_pct)

    def close_position(self) -> None:
        self._cancel_exit_orders()
        self.close()

    def _is_entry_completion(self, order: bt.Order) -> bool:
        return self._orders_match(order, self.entry_order) and order.status == order.Completed

    def _is_exit_completion(self, order: bt.Order) -> bool:
        return (
            self._orders_match(order, self.stop_order)
            or self._orders_match(order, self.take_profit_order)
            or (order.issell() and not self.position)
        )

    def _is_pending_entry_order(self, order: bt.Order) -> bool:
        return self._orders_match(order, self.entry_order)

    def _submit_exit_orders(self, entry_price: float, size: float) -> None:
        stop_price = entry_price * (1.0 - self.p.stop_loss_pct)
        take_profit_price = self.get_long_take_profit_price(entry_price=entry_price)

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

    def _cancel_exit_orders(self) -> None:
        for order in (self.stop_order, self.take_profit_order):
            self._cancel_order_if_active(order)
        self._clear_exit_orders()

    def _clear_exit_orders(self) -> None:
        self.stop_order = None
        self.take_profit_order = None

    def _cancel_order_if_active(self, order: Optional[bt.Order]) -> None:
        if order and order.status not in (bt.Order.Canceled, bt.Order.Completed, bt.Order.Rejected):
            self.cancel(order)

    @staticmethod
    def _orders_match(left: Optional[bt.Order], right: Optional[bt.Order]) -> bool:
        if left is None or right is None:
            return False
        return getattr(left, "ref", None) == getattr(right, "ref", None)

    def should_enter_long(self) -> bool:
        raise NotImplementedError

    def should_exit_long(self) -> bool:
        raise NotImplementedError
