from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import backtrader as bt
import pandas as pd

from engine.metrics import BacktestMetrics, build_metrics
from engine.plotting import plot_equity_curve, plot_trade_chart


class PandasOHLCVData(bt.feeds.PandasData):
    params = (
        ("datetime", None),
        ("open", "Open"),
        ("high", "High"),
        ("low", "Low"),
        ("close", "Close"),
        ("volume", "Volume"),
        ("openinterest", -1),
    )


@dataclass(slots=True)
class BacktestRunResult:
    metrics: BacktestMetrics
    equity_curve: pd.Series
    chart_paths: dict[str, Path] = field(default_factory=dict)
    final_portfolio_value: float = 0.0


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float,
        commission: float,
        slippage_perc: float,
        output_dir: Path,
    ) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage_perc = slippage_perc
        self.output_dir = output_dir

    def run(
        self,
        dataframe: pd.DataFrame,
        strategy_class: type[bt.Strategy],
        strategy_params: dict[str, Any],
        extra_dataframes: list[pd.DataFrame] | None = None,
        plot_results: bool = True,
        base_timeframe: str = "1d",
        resample_rules: list[dict[str, int]] | None = None,
    ) -> BacktestRunResult:
        cerebro = bt.Cerebro(stdstats=True, cheat_on_open=False)
        cerebro.broker.setcash(self.initial_capital)
        cerebro.broker.setcommission(commission=self.commission)
        cerebro.broker.set_slippage_perc(self.slippage_perc, slip_open=True, slip_limit=True, slip_match=True)

        data_feed = PandasOHLCVData(dataname=dataframe)
        primary_feed = self._configure_data_feed(data_feed=data_feed, timeframe=base_timeframe)
        cerebro.adddata(primary_feed)
        for extra_dataframe in extra_dataframes or []:
            extra_feed = PandasOHLCVData(dataname=extra_dataframe)
            cerebro.adddata(self._configure_data_feed(data_feed=extra_feed, timeframe=base_timeframe))
        for rule in resample_rules or []:
            cerebro.resampledata(
                primary_feed,
                timeframe=rule["timeframe"],
                compression=rule["compression"],
                boundoff=0,
            )
        cerebro.addstrategy(strategy_class, **strategy_params)

        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade_analyzer")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(
            bt.analyzers.SharpeRatio,
            _name="sharpe",
            timeframe=bt.TimeFrame.Days,
            annualize=True,
            riskfreerate=0.0,
        )
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="time_return")

        strategies = cerebro.run()
        strategy = strategies[0]
        final_value = float(cerebro.broker.getvalue())

        trade_analysis = strategy.analyzers.trade_analyzer.get_analysis()
        drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
        sharpe_analysis = strategy.analyzers.sharpe.get_analysis()
        returns_analysis = strategy.analyzers.time_return.get_analysis()
        trade_journal = getattr(strategy, "trade_journal", None)
        trades_dataframe = trade_journal.to_dataframe() if trade_journal is not None else None

        equity_curve = self._build_equity_curve(returns_analysis)
        metrics = build_metrics(
            initial_capital=self.initial_capital,
            final_value=final_value,
            trade_analysis=trade_analysis,
            drawdown_analysis=drawdown_analysis,
            sharpe_analysis=sharpe_analysis,
            trades_dataframe=trades_dataframe,
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if trade_journal is not None:
            trade_journal.to_csv(self.output_dir / "trades.csv")

        chart_paths: dict[str, Path] = {}
        if plot_results:
            chart_paths.update(self._render_charts(dataframe, strategy, equity_curve, strategy_params))

        return BacktestRunResult(
            metrics=metrics,
            equity_curve=equity_curve,
            chart_paths=chart_paths,
            final_portfolio_value=final_value,
        )

    def _configure_data_feed(self, data_feed: PandasOHLCVData, timeframe: str) -> PandasOHLCVData:
        if timeframe.endswith("m"):
            data_feed._timeframe = bt.TimeFrame.Minutes
            data_feed._compression = int(timeframe[:-1])
            return data_feed
        if timeframe.endswith("h"):
            data_feed._timeframe = bt.TimeFrame.Minutes
            data_feed._compression = int(timeframe[:-1]) * 60
            return data_feed
        if timeframe == "1d":
            data_feed._timeframe = bt.TimeFrame.Days
            data_feed._compression = 1
            return data_feed
        if timeframe == "5d":
            data_feed._timeframe = bt.TimeFrame.Days
            data_feed._compression = 5
            return data_feed
        if timeframe == "1wk":
            data_feed._timeframe = bt.TimeFrame.Weeks
            data_feed._compression = 1
            return data_feed
        if timeframe == "1mo":
            data_feed._timeframe = bt.TimeFrame.Months
            data_feed._compression = 1
            return data_feed
        if timeframe == "3mo":
            data_feed._timeframe = bt.TimeFrame.Months
            data_feed._compression = 3
            return data_feed
        raise ValueError(f"Unsupported base timeframe for engine: {timeframe}")

    def _render_charts(
        self,
        dataframe: pd.DataFrame,
        strategy: bt.Strategy,
        equity_curve: pd.Series,
        strategy_params: dict[str, Any],
    ) -> dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        chart_paths: dict[str, Path] = {}

        equity_path = plot_equity_curve(equity_curve, self.output_dir / "equity_curve.png")
        chart_paths["equity_curve"] = equity_path

        trade_path = plot_trade_chart(
            market_data=dataframe,
            buy_markers=getattr(strategy, "buy_markers", []),
            sell_markers=getattr(strategy, "sell_markers", []),
            output_path=self.output_dir / "trades_chart.png",
            fast_period=strategy_params.get("fast_period"),
            slow_period=strategy_params.get("slow_period"),
        )
        chart_paths["trades_chart"] = trade_path

        return chart_paths

    def _build_equity_curve(self, returns_analysis: dict[Any, float]) -> pd.Series:
        if not returns_analysis:
            return pd.Series([self.initial_capital], name="equity")

        returns_series = pd.Series(returns_analysis).sort_index()
        equity_curve = (1.0 + returns_series).cumprod() * self.initial_capital
        equity_curve.name = "equity"
        return equity_curve
