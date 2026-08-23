from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import backtrader as bt
import pandas as pd


@dataclass(slots=True)
class TradeRecord:
    entry_time: datetime | None
    exit_time: datetime | None
    direction: str
    entry_price: float
    exit_price: float | None
    stop_loss: float
    take_profit: float
    position_size: float
    pnl_dollars: float | None
    pnl_percent: float | None
    R_multiple: float | None
    trade_duration_bars: int | None
    exit_reason: str
    ema50_slope: float | None = None
    ema200_slope: float | None = None
    distance_above_ema50: float | None = None
    distance_above_ema200: float | None = None
    rs20: float | None = None
    rs60: float | None = None
    rs120: float | None = None
    atr14: float | None = None
    atr_percent: float | None = None
    daily_range_percent: float | None = None
    true_range: float | None = None
    breakout_distance: float | None = None
    previous_20_bar_high: float | None = None
    days_since_last_breakout: int | None = None
    volume: float | None = None
    average_volume20: float | None = None
    relative_volume: float | None = None
    spy_trend: float | None = None
    spy_above_ema200: bool | None = None
    spy_return60: float | None = None
    entry_atr: float | None = None
    initial_risk: float | None = None
    holding_days: int | None = None
    mae: float | None = None
    mfe: float | None = None


@dataclass(slots=True)
class TradePlan:
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: str
    position_size: float


class TradeJournal:
    def __init__(self) -> None:
        self.records: list[TradeRecord] = []
        self._open_trade: TradeRecord | None = None
        self._open_trade_key: object | None = None
        self._open_trades: dict[object | None, TradeRecord] = {}
        self._pending_plans: deque[tuple[object | None, TradePlan]] = deque()

    def register_trade_plan(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        position_size: float,
        plan_key: object | None = None,
    ) -> None:
        self._pending_plans.append(
            (
                plan_key,
                TradePlan(
                    entry_price=float(entry_price),
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    direction=str(direction).upper(),
                    position_size=float(position_size),
                ),
            )
        )

    def clear_pending_trade_plan(self, plan_key: object | None = None) -> None:
        if not self._pending_plans:
            return
        if plan_key is None:
            self._pending_plans.pop()
            return

        for index in range(len(self._pending_plans) - 1, -1, -1):
            pending_key, _ = self._pending_plans[index]
            if pending_key == plan_key:
                del self._pending_plans[index]
                return

    def record_entry(
        self,
        entry_time: datetime | None,
        entry_price: float,
        direction: str,
        position_size: float,
        stop_loss: float,
        take_profit: float,
        trade_key: object | None = None,
        research_features: dict[str, Any] | None = None,
    ) -> None:
        trade_record = TradeRecord(
            entry_time=entry_time,
            exit_time=None,
            direction=direction.upper(),
            entry_price=float(entry_price),
            exit_price=None,
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            position_size=float(position_size),
            pnl_dollars=None,
            pnl_percent=None,
            R_multiple=None,
            trade_duration_bars=None,
            exit_reason="UNKNOWN",
        )
        self._apply_research_features(trade_record, research_features)
        self._open_trades[trade_key] = trade_record
        self._open_trade_key = trade_key
        self._sync_legacy_open_trade()

    def record_exit(
        self,
        exit_time: datetime | None,
        exit_price: float,
        pnl_dollars: float,
        pnl_percent: float | None,
        r_multiple: float | None,
        trade_duration_bars: int | None,
        exit_reason: str,
        trade_key: object | None = None,
        research_features: dict[str, Any] | None = None,
    ) -> None:
        resolved_trade_key = self._resolve_trade_key(trade_key)
        if resolved_trade_key is None:
            return
        open_trade = self._open_trades.get(resolved_trade_key)
        if open_trade is None:
            return

        open_trade.exit_time = exit_time
        open_trade.exit_price = float(exit_price)
        open_trade.pnl_dollars = float(pnl_dollars)
        open_trade.pnl_percent = float(pnl_percent) if pnl_percent is not None else None
        open_trade.R_multiple = float(r_multiple) if r_multiple is not None else None
        open_trade.trade_duration_bars = int(trade_duration_bars) if trade_duration_bars is not None else None
        open_trade.exit_reason = exit_reason
        self._apply_research_features(open_trade, research_features)
        self.records.append(open_trade)
        del self._open_trades[resolved_trade_key]
        if self._open_trade_key == resolved_trade_key:
            self._open_trade_key = next(iter(self._open_trades), None)
        self._sync_legacy_open_trade()

    def update_trade_metadata(self, trade_key: object | None, **features: Any) -> None:
        trade = self.get_open_trade(trade_key)
        if trade is not None:
            self._apply_research_features(trade, features)

    @staticmethod
    def _apply_research_features(trade: TradeRecord, features: dict[str, Any] | None) -> None:
        if not features:
            return
        valid_fields = TradeRecord.__dataclass_fields__
        for name, value in features.items():
            if name in valid_fields and name not in {
                "entry_time", "exit_time", "direction", "entry_price", "exit_price",
                "stop_loss", "take_profit", "position_size", "pnl_dollars",
                "pnl_percent", "R_multiple", "trade_duration_bars", "exit_reason",
            }:
                setattr(trade, name, value)

    def pop_trade_plan(self, plan_key: object | None = None) -> TradePlan | None:
        if not self._pending_plans:
            return None
        if plan_key is None:
            return self._pending_plans.popleft()[1]

        for index, (pending_key, plan) in enumerate(self._pending_plans):
            if pending_key == plan_key:
                del self._pending_plans[index]
                return plan
        return None

    def get_open_trade(self, trade_key: object | None = None) -> TradeRecord | None:
        resolved_trade_key = self._resolve_trade_key(trade_key)
        if resolved_trade_key is None:
            return None
        return self._open_trades.get(resolved_trade_key)

    def update_open_trade_plan(
        self,
        trade_key: object | None,
        *,
        entry_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        position_size: float | None = None,
    ) -> None:
        trade_record = self.get_open_trade(trade_key)
        if trade_record is None:
            return
        if entry_price is not None:
            trade_record.entry_price = float(entry_price)
        if stop_loss is not None:
            trade_record.stop_loss = float(stop_loss)
        if take_profit is not None:
            trade_record.take_profit = float(take_profit)
        if position_size is not None:
            trade_record.position_size = float(position_size)

    def to_dataframe(self) -> pd.DataFrame:
        columns = [field_name for field_name in TradeRecord.__dataclass_fields__]
        if not self.records:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame([asdict(record) for record in self.records], columns=columns)

    def to_csv(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(output_path, index=False)
        return output_path

    def _resolve_trade_key(self, trade_key: object | None) -> object | None:
        if trade_key in self._open_trades:
            return trade_key
        if trade_key is None and self._open_trade_key in self._open_trades:
            return self._open_trade_key
        if len(self._open_trades) == 1:
            return next(iter(self._open_trades))
        return None

    def _sync_legacy_open_trade(self) -> None:
        self._open_trade = self._open_trades.get(self._open_trade_key)
        if self._open_trade is None and self._open_trades:
            self._open_trade_key, self._open_trade = next(iter(self._open_trades.items()))
        if not self._open_trades:
            self._open_trade_key = None
            self._open_trade = None


class TradeJournalMixin:
    journal_price_tolerance = 0.001

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.trade_journal = TradeJournal()
        self._journal_active_plan: TradePlan | None = None
        self._journal_active_plans: dict[object | None, TradePlan] = {}
        self._journal_last_exit_dt: datetime | None = None
        self._journal_last_exit_price: float | None = None
        self._journal_last_exit_kind: str | None = None  # STOP / LIMIT / MARKET / OTHER
        self._journal_last_exit_info: dict[object | None, tuple[datetime | None, float | None, str | None]] = {}
        self._journal_current_trade_key: object | None = None
        super().__init__(*args, **kwargs)

    def register_trade_plan(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        position_size: float,
        plan_key: object | None = None,
    ) -> None:
        self.trade_journal.register_trade_plan(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            direction=direction,
            position_size=position_size,
            plan_key=plan_key,
        )

    def update_trade_plan(
        self,
        trade_key: object | None,
        *,
        entry_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        position_size: float | None = None,
    ) -> None:
        plan = self._journal_active_plans.get(trade_key)
        if plan is not None:
            if entry_price is not None:
                plan.entry_price = float(entry_price)
            if stop_loss is not None:
                plan.stop_loss = float(stop_loss)
            if take_profit is not None:
                plan.take_profit = float(take_profit)
            if position_size is not None:
                plan.position_size = float(position_size)

        self.trade_journal.update_open_trade_plan(
            trade_key,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
        )

    def update_trade_metadata(self, trade_key: object | None, **features: Any) -> None:
        self.trade_journal.update_trade_metadata(trade_key, **features)

    def notify_order(self, order: bt.Order) -> None:
        trade_key = self._trade_key_from_order(order)
        if order.status == order.Completed:
            if self._is_entry_completion(order):
                plan = self.trade_journal.pop_trade_plan(plan_key=trade_key)
                if plan is None:
                    plan = self.trade_journal.pop_trade_plan()
                if plan is not None:
                    self._journal_active_plan = plan
                    self._journal_active_plans[trade_key] = plan
            elif self._is_exit_completion(order):
                self._journal_last_exit_dt = bt.num2date(order.executed.dt) if order.executed.dt else None
                executed_price = float(order.executed.price) if order.executed.price else None
                fallback_price = self._infer_order_price(order)
                self._journal_last_exit_price = executed_price if executed_price is not None else fallback_price

                exectype = getattr(order, "exectype", None)
                if exectype == bt.Order.Stop:
                    self._journal_last_exit_kind = "STOP"
                elif exectype == bt.Order.Limit:
                    self._journal_last_exit_kind = "LIMIT"
                elif exectype == bt.Order.Market:
                    self._journal_last_exit_kind = "MARKET"
                else:
                    self._journal_last_exit_kind = "OTHER"
                self._journal_last_exit_info[trade_key] = (
                    self._journal_last_exit_dt,
                    self._journal_last_exit_price,
                    self._journal_last_exit_kind,
                )

        if order.status in (order.Canceled, order.Margin, order.Rejected):
            if self._is_pending_entry_order(order):
                self.trade_journal.clear_pending_trade_plan(plan_key=trade_key)

        super().notify_order(order)

    def notify_trade(self, trade: bt.Trade) -> None:
        trade_key = self._trade_key_from_trade(trade)
        if trade.justopened:
            plan = self._journal_active_plans.get(trade_key)
            if plan is None:
                plan = self.trade_journal.pop_trade_plan(plan_key=trade_key)
                if plan is None:
                    plan = self.trade_journal.pop_trade_plan()
                if plan is not None:
                    self._journal_active_plan = plan
                    self._journal_active_plans[trade_key] = plan
            if plan is not None:
                research_features = getattr(self, "_journal_entry_research_features", {}).get(trade_key, {})
                self.trade_journal.record_entry(
                    entry_time=bt.num2date(trade.dtopen) if trade.dtopen else None,
                    entry_price=float(trade.price),
                    direction=plan.direction,
                    position_size=float(abs(trade.size)) if trade.size else plan.position_size,
                    stop_loss=plan.stop_loss,
                    take_profit=plan.take_profit,
                    trade_key=trade_key,
                    research_features=research_features,
                )

        if trade.isclosed:
            plan = self._journal_active_plans.get(trade_key)
            open_trade = self.trade_journal.get_open_trade(trade_key)
            if plan is None and open_trade is not None:
                plan = TradePlan(
                    entry_price=open_trade.entry_price,
                    stop_loss=open_trade.stop_loss,
                    take_profit=open_trade.take_profit,
                    direction=open_trade.direction,
                    position_size=open_trade.position_size,
                )
            if plan is not None:
                exit_dt, exit_price, exit_kind = self._journal_last_exit_info.pop(trade_key, (None, None, None))
                self._journal_last_exit_dt = exit_dt
                self._journal_last_exit_price = exit_price
                self._journal_last_exit_kind = exit_kind
                if exit_price is None:
                    exit_price = self._fallback_trade_exit_price(trade=trade, plan=plan)

                pnl_dollars = float(trade.pnlcomm)
                exposure = abs(plan.entry_price * plan.position_size)
                pnl_percent = (pnl_dollars / exposure * 100.0) if exposure > 0 else None
                initial_risk = abs(plan.entry_price - plan.stop_loss) * abs(plan.position_size)
                r_multiple = (pnl_dollars / initial_risk) if initial_risk > 0 else None
                self._journal_current_trade_key = trade_key
                exit_reason = self._classify_exit_reason(exit_price=exit_price, plan=plan)
                self.trade_journal.record_exit(
                    exit_time=self._journal_last_exit_dt or (bt.num2date(trade.dtclose) if trade.dtclose else None),
                    exit_price=exit_price,
                    pnl_dollars=pnl_dollars,
                    pnl_percent=pnl_percent,
                    r_multiple=r_multiple,
                    trade_duration_bars=int(trade.barlen) if trade.barlen is not None else None,
                    exit_reason=exit_reason,
                    trade_key=trade_key,
                    research_features={
                        "holding_days": int(trade.barlen) if trade.barlen is not None else None,
                    },
                )
                self._journal_active_plans.pop(trade_key, None)
                getattr(self, "_journal_entry_research_features", {}).pop(trade_key, None)
                self._journal_active_plan = next(iter(self._journal_active_plans.values()), None)
                self._journal_current_trade_key = None

            self._journal_last_exit_dt = None
            self._journal_last_exit_price = None
            self._journal_last_exit_kind = None

        super().notify_trade(trade)

    def _classify_exit_reason(self, exit_price: float, plan: TradePlan) -> str:
        if exit_price is None:
            return "UNKNOWN"
        if not (exit_price == exit_price):  # NaN guard
            return "UNKNOWN"

        # 1) Exact-ish price match first (0.1% tolerance)
        if self._price_matches(exit_price, plan.take_profit):
            return "TP"
        if self._price_matches(exit_price, plan.stop_loss):
            return "SL"

        # 2) If not near TP/SL, fall back to how we exited.
        # Trailing-stop / protective-stop exits are STOP-type orders -> SL bucket.
        if self._journal_last_exit_kind == "LIMIT":
            return "TP"
        if self._journal_last_exit_kind == "STOP":
            return "SL"

        # 3) Last resort only.
        return "UNKNOWN"

    def _price_matches(self, actual: float, expected: float) -> bool:
        tolerance = abs(expected) * self.journal_price_tolerance
        tolerance = max(tolerance, 1e-8)
        return abs(actual - expected) <= tolerance

    def _fallback_trade_exit_price(self, trade: bt.Trade, plan: TradePlan) -> float:
        if self._price_matches(plan.stop_loss, plan.take_profit):
            return plan.stop_loss
        if float(trade.pnlcomm) >= 0:
            return plan.take_profit
        return plan.stop_loss

    def _infer_order_price(self, order: bt.Order) -> float | None:
        created_price = getattr(order.created, "price", None)
        if created_price:
            return float(created_price)
        return None

    def _trade_key_from_order(self, order: bt.Order) -> object | None:
        tradeid = getattr(order, "tradeid", None)
        if tradeid is not None:
            return tradeid
        return getattr(order, "ref", None)

    def _trade_key_from_trade(self, trade: bt.Trade) -> object | None:
        tradeid = getattr(trade, "tradeid", None)
        if tradeid is not None:
            return tradeid
        return getattr(trade, "ref", None)

    def _is_entry_completion(self, order: bt.Order) -> bool:
        return False

    def _is_exit_completion(self, order: bt.Order) -> bool:
        return False

    def _is_pending_entry_order(self, order: bt.Order) -> bool:
        return False
