from __future__ import annotations

import backtrader as bt

from engine.trade_journal import TradeJournalMixin, TradePlan


class LeadershipExpansionV1Strategy(TradeJournalMixin, bt.Strategy):
    """Leadership + relative strength + volatility expansion research strategy."""

    params = (
        ("risk_per_trade", 0.01),
        ("ema_trend_period", 200),
        ("ema_quality_period", 50),
        ("atr_period", 14),
        ("relative_strength_lookback", 60),
        ("relative_strength_threshold", 0.05),
        ("expansion_atr_multiple", 1.5),
        ("breakout_lookback", 20),
        ("initial_stop_atr_multiple", 1.5),
        ("trailing_stop_atr_multiple", 2.0),
        ("max_holding_bars", 60),
        ("max_positions", 3),
        ("skip_relative_strength_filter", False),
        ("enable_leadership_quality", True),
        # Research-only switches. Defaults preserve the production baseline.
        ("enable_relative_strength_filter", True),
        ("enable_ema200_filter", True),
        ("enable_ema200_slope_filter", True),
        ("enable_ema50_filter", True),
        ("enable_expansion_filter", True),
        ("enable_breakout_confirmation", True),
        ("enable_protective_stop_exit", True),
        ("enable_atr_trailing_exit", True),
        ("enable_ema_exit", True),
        ("enable_time_exit", True),
        ("enable_risk_position_sizing", True),
    )

    def __init__(self) -> None:
        super().__init__()
        if len(self.datas) < 2:
            raise ValueError("leadership_expansion_v1 requires stock and benchmark feeds.")

        self.data_stock = self.datas[0]
        self.data_benchmark = self.datas[1]

        self.ema200 = bt.indicators.ExponentialMovingAverage(self.data_stock.close, period=self.p.ema_trend_period)
        self.ema50 = bt.indicators.ExponentialMovingAverage(self.data_stock.close, period=self.p.ema_quality_period)
        self.atr = bt.indicators.AverageTrueRange(self.data_stock, period=self.p.atr_period)
        self.true_range = bt.indicators.TrueRange(self.data_stock)

        self.next_trade_id = 1
        self.pending_entries: dict[int, bt.Order] = {}
        self.exit_orders: dict[int, bt.Order] = {}
        self.active_sizes: dict[int, int] = {}
        self.planned_stops: dict[int, float] = {}
        self.entry_bars: dict[int, int] = {}
        self.initial_stops: dict[int, float] = {}
        self.current_stops: dict[int, float] = {}
        self.pending_exit_reasons: dict[int, str] = {}
        self._journal_entry_research_features: dict[int, dict[str, object]] = {}
        self._pending_research_features: dict[int, dict[str, object]] = {}
        self.buy_markers: list[tuple[object, float]] = []
        self.sell_markers: list[tuple[object, float]] = []

    def next(self) -> None:
        self._manage_open_trades()

        if self._active_trade_count() >= self.p.max_positions:
            return
        if not self._should_enter_long():
            return

        reference_price = float(self.data_stock.close[0])
        current_atr = float(self.atr[0])
        stop_price = reference_price - (current_atr * self.p.initial_stop_atr_multiple)
        if current_atr <= 0 or stop_price <= 0 or reference_price <= stop_price:
            return

        size = self.calculate_position_size(reference_price=reference_price, stop_price=stop_price)
        if size <= 0:
            return

        trade_id = self.next_trade_id
        self.next_trade_id += 1
        self.register_trade_plan(
            entry_price=reference_price,
            stop_loss=stop_price,
            take_profit=reference_price,
            direction="LONG",
            position_size=size,
            plan_key=trade_id,
        )
        self.planned_stops[trade_id] = stop_price
        self._pending_research_features[trade_id] = self._entry_research_features(reference_price)
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
                initial_stop = entry_price - (float(self.atr[0]) * self.p.initial_stop_atr_multiple)
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
                research_features = self._pending_research_features.pop(trade_id, {})
                research_features["initial_risk"] = abs(entry_price - initial_stop)
                self._journal_entry_research_features[trade_id] = research_features
                self.update_trade_plan(
                    trade_id,
                    entry_price=entry_price,
                    stop_loss=initial_stop,
                    take_profit=entry_price,
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
                self._pending_research_features.pop(trade_id, None)
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
        if not self.p.enable_risk_position_sizing:
            return 1 if self.broker.getcash() >= reference_price else 0

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
        current_low = float(self.data_stock.low[0])
        current_atr = float(self.atr[0])
        ema50_level = float(self.ema50[0])
        if current_atr <= 0:
            return

        for trade_id, size in list(self.active_sizes.items()):
            if size <= 0 or trade_id in self.exit_orders:
                continue

            if self.p.enable_atr_trailing_exit:
                trailing_stop = current_close - (current_atr * self.p.trailing_stop_atr_multiple)
                if trailing_stop > self.current_stops.get(trade_id, 0.0):
                    self.current_stops[trade_id] = trailing_stop

            exit_reason = None
            current_stop = self.current_stops.get(trade_id, 0.0)
            initial_stop = self.initial_stops.get(trade_id, current_stop)

            # Excursions are research metadata only; they do not affect orders.
            initial_risk = max(self.active_entry_price(trade_id) - initial_stop, 0.0)
            if initial_risk > 0:
                trade = self.trade_journal.get_open_trade(trade_id)
                if trade is not None:
                    mfe = (current_high := float(self.data_stock.high[0])) - trade.entry_price
                    mae = float(self.data_stock.low[0]) - trade.entry_price
                    self.update_trade_metadata(
                        trade_id,
                        mfe=max(float(trade.mfe or 0.0), mfe / initial_risk),
                        mae=min(float(trade.mae or 0.0), mae / initial_risk),
                    )

            trailing_stop_active = current_stop > initial_stop + 1e-8
            if current_low <= current_stop and (
                (trailing_stop_active and self.p.enable_atr_trailing_exit)
                or (not trailing_stop_active and self.p.enable_protective_stop_exit)
            ):
                exit_reason = "ATR_TRAIL" if trailing_stop_active else "STOP"
            elif self.p.enable_ema_exit and current_close < ema50_level:
                exit_reason = "EMA_EXIT"
            elif self.p.enable_time_exit and len(self) - self.entry_bars.get(trade_id, len(self)) >= self.p.max_holding_bars:
                exit_reason = "TIME_EXIT"

            if exit_reason is None:
                continue

            self.pending_exit_reasons[trade_id] = exit_reason
            self.exit_orders[trade_id] = self.sell(size=size, tradeid=trade_id)

    def active_entry_price(self, trade_id: int) -> float:
        trade = self.trade_journal.get_open_trade(trade_id)
        if trade is not None:
            return trade.entry_price
        return float(self.data_stock.close[0])

    def _entry_research_features(self, entry_price: float) -> dict[str, object]:
        close = float(self.data_stock.close[0])
        high = float(self.data_stock.high[0])
        low = float(self.data_stock.low[0])
        volume = float(self.data_stock.volume[0])
        atr = float(self.atr[0])
        ema50 = float(self.ema50[0])
        ema200 = float(self.ema200[0])
        previous_high = max(float(self.data_stock.high[-bar]) for bar in range(1, 21))
        avg_volume20 = self._average_line(self.data_stock.volume, 20)
        benchmark_close = float(self.data_benchmark.close[0])
        spy_ema200 = self._benchmark_ema200()

        features: dict[str, object] = {
            "ema50_slope": ema50 - float(self.ema50[-1]),
            "ema200_slope": ema200 - float(self.ema200[-1]),
            "distance_above_ema50": (entry_price - ema50) / atr if atr > 0 else None,
            "distance_above_ema200": (entry_price - ema200) / atr if atr > 0 else None,
            "rs20": self._relative_strength(20),
            "rs60": self._relative_strength(60),
            "rs120": self._relative_strength(120),
            "atr14": atr,
            "atr_percent": atr / entry_price if entry_price > 0 else None,
            "daily_range_percent": (high - low) / entry_price if entry_price > 0 else None,
            "true_range": float(self.true_range[0]),
            "breakout_distance": (close / previous_high) - 1.0 if previous_high > 0 else None,
            "previous_20_bar_high": previous_high,
            "days_since_last_breakout": self._days_since_last_breakout(),
            "volume": volume,
            "average_volume20": avg_volume20,
            "relative_volume": volume / avg_volume20 if avg_volume20 > 0 else None,
            "spy_trend": spy_ema200 - self._benchmark_ema200_previous(),
            "spy_above_ema200": benchmark_close > spy_ema200,
            "spy_return60": self._benchmark_return(60),
            "entry_atr": atr,
            "initial_risk": abs(entry_price - (entry_price - atr * self.p.initial_stop_atr_multiple)),
            "mae": 0.0,
            "mfe": 0.0,
        }
        return features

    def _relative_strength(self, lookback: int) -> float:
        return self._stock_return(float(self.data_stock.close[0]), lookback) - self._benchmark_return(lookback)

    def _average_line(self, line: object, period: int) -> float:
        values = [float(line[-offset]) for offset in range(period)]
        return sum(values) / period

    def _benchmark_ema200(self) -> float:
        closes = [float(self.data_benchmark.close[-offset]) for offset in range(199, -1, -1)]
        alpha = 2.0 / 201.0
        ema = closes[0]
        for value in closes[1:]:
            ema = alpha * value + (1.0 - alpha) * ema
        return ema

    def _benchmark_ema200_previous(self) -> float:
        closes = [float(self.data_benchmark.close[-offset]) for offset in range(200, 0, -1)]
        alpha = 2.0 / 201.0
        ema = closes[0]
        for value in closes[1:]:
            ema = alpha * value + (1.0 - alpha) * ema
        return ema

    def _days_since_last_breakout(self) -> int | None:
        for days_ago in range(1, min(len(self), 252)):
            if days_ago + self.p.breakout_lookback >= len(self):
                break
            prior_high = max(
                float(self.data_stock.close[-days_ago - offset])
                for offset in range(1, self.p.breakout_lookback + 1)
            )
            if float(self.data_stock.close[-days_ago]) > prior_high:
                return days_ago
        return None

    def _should_enter_long(self) -> bool:
        required_bars = max(
            self.p.ema_trend_period + 1,
            self.p.ema_quality_period,
            self.p.atr_period + 1,
            self.p.relative_strength_lookback + 1,
            121,
            self.p.breakout_lookback + 1,
        )
        if len(self) < required_bars or len(self.data_benchmark) < required_bars:
            return False

        close_price = float(self.data_stock.close[0])
        ema200 = float(self.ema200[0])
        ema200_prev = float(self.ema200[-1])
        ema50 = float(self.ema50[0])
        atr_value = float(self.atr[0])
        true_range = float(self.true_range[0])
        if atr_value <= 0:
            return False

        if self.p.enable_ema200_filter and close_price <= ema200:
            return False
        if self.p.enable_ema200_slope_filter and ema200 <= ema200_prev:
            return False
        if self.p.enable_ema50_filter and close_price <= ema50:
            return False

        if self.p.enable_relative_strength_filter and not self.p.skip_relative_strength_filter:
            if not self._passes_relative_strength(close_price):
                return False

        if self.p.enable_expansion_filter and true_range <= self.p.expansion_atr_multiple * atr_value:
            return False

        highest_close = max(float(self.data_stock.close[-bar]) for bar in range(1, self.p.breakout_lookback + 1))
        return not self.p.enable_breakout_confirmation or close_price > highest_close

    def _passes_relative_strength(self, close_price: float) -> bool:
        stock_return_60 = self._stock_return(close_price=close_price, lookback=self.p.relative_strength_lookback)
        benchmark_return_60 = self._benchmark_return(lookback=self.p.relative_strength_lookback)
        rs60 = stock_return_60 - benchmark_return_60
        if stock_return_60 <= benchmark_return_60:
            return False
        if rs60 <= self.p.relative_strength_threshold:
            return False
        if not self.p.enable_leadership_quality:
            return True

        rs20 = self._stock_return(close_price=close_price, lookback=20) - self._benchmark_return(lookback=20)
        rs120 = self._stock_return(close_price=close_price, lookback=120) - self._benchmark_return(lookback=120)
        return rs20 > 0.0 or rs120 > 0.10

    def _stock_return(self, close_price: float, lookback: int) -> float:
        return (close_price / float(self.data_stock.close[-lookback])) - 1.0

    def _benchmark_return(self, lookback: int) -> float:
        return (float(self.data_benchmark.close[0]) / float(self.data_benchmark.close[-lookback])) - 1.0

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

    def _active_trade_count(self) -> int:
        return len(self.active_sizes) + len(self.pending_entries)
