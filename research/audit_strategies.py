"""Read-only Backtrader strategies used by descriptive research audits."""

from __future__ import annotations

import backtrader as bt

from strategies.leadership_expansion_v1 import LeadershipExpansionV1Strategy


class LeadershipExpansionEligibilityAuditStrategy(LeadershipExpansionV1Strategy):
    """Records the production entry-filter states without submitting orders."""

    def __init__(self) -> None:
        super().__init__()
        self.candidate_records: list[dict[str, object]] = []

    def next(self) -> None:
        required_bars = max(
            self.p.ema_trend_period + 1,
            self.p.ema_quality_period,
            self.p.atr_period + 1,
            self.p.relative_strength_lookback + 1,
            121,
            self.p.breakout_lookback + 1,
        )
        if len(self) < required_bars or len(self.data_benchmark) < required_bars:
            return

        close_price = float(self.data_stock.close[0])
        ema200 = float(self.ema200[0])
        ema200_prev = float(self.ema200[-1])
        ema50 = float(self.ema50[0])
        atr_value = float(self.atr[0])
        true_range = float(self.true_range[0])
        if atr_value <= 0:
            return

        stock_return60 = self._stock_return(close_price, self.p.relative_strength_lookback)
        benchmark_return60 = self._benchmark_return(self.p.relative_strength_lookback)
        rs60 = stock_return60 - benchmark_return60
        rs20 = self._relative_strength(20)
        rs120 = self._relative_strength(120)
        highest_close = max(float(self.data_stock.close[-bar]) for bar in range(1, self.p.breakout_lookback + 1))

        states = {
            "relative_strength_pass": stock_return60 > benchmark_return60 and rs60 > self.p.relative_strength_threshold,
            "leadership_quality_pass": rs20 > 0.0 or rs120 > 0.10,
            "ema200_price_pass": close_price > ema200,
            "ema200_slope_pass": ema200 > ema200_prev,
            "ema50_price_pass": close_price > ema50,
            "atr_expansion_pass": true_range > self.p.expansion_atr_multiple * atr_value,
            "breakout_confirmation_pass": close_price > highest_close,
        }
        failed_components = [
            name.removesuffix("_pass").upper()
            for name, passed in states.items()
            if not passed
        ]
        self.candidate_records.append(
            {
                "date": self.data_stock.datetime.date(0).isoformat(),
                **states,
                "accepted": not failed_components,
                "rejected": bool(failed_components),
                "failing_components": "{" + ", ".join(failed_components) + "}" if failed_components else "{}",
            }
        )


class LeadershipExpansionOOSWarmupStrategy(LeadershipExpansionV1Strategy):
    """Production strategy with an entry-free indicator warmup period for OOS research."""

    params = (("entry_start_date", None),)

    def next(self) -> None:
        start = self.p.entry_start_date
        if start is not None and bt.num2date(self.data_stock.datetime[0]).date().isoformat() < start:
            return
        super().next()
