from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import argparse
import os

import backtrader as bt
import pandas as pd

from config.settings import BacktestConfig, load_config
from daily_signal_report import SignalRecord, write_daily_signal_report
from data.yahoo_data import MarketDataRequest, YahooFinanceDataSource
from engine.backtest_engine import PandasOHLCVData
from logging_system import DailyRunLogger
from main import build_strategy_params
from paper_performance_dashboard import append_daily_performance
from startup_checks import assert_startup_checks
from strategies.leadership_expansion_v1 import LeadershipExpansionV1Strategy
from telegram_notifier import TelegramNotifier
from verify_strategy_execution import build_execution_verification, write_execution_verification


STRATEGY_NAME = "leadership_expansion_v1"
PORTFOLIO_PATH = Path("paper_portfolio.csv")
PAPER_UNIVERSE_PATH = Path("config") / "paper_universe.csv"
UNIVERSE_PATH = Path("output") / "universe_membership.csv"
PORTFOLIO_COLUMNS = [
    "strategy_name",
    "ticker",
    "status",
    "entry_date",
    "exit_date",
    "entry_price",
    "exit_price",
    "stop_price",
    "position_size",
    "risk_per_trade",
    "R_multiple",
    "PnL",
    "current_equity",
    "drawdown",
    "last_updated",
    "exit_reason",
]


@dataclass(slots=True)
class SymbolRunResult:
    ticker: str
    latest_date: str | None
    latest_close: float | None
    signals: list[SignalRecord]
    closed_trades: pd.DataFrame
    open_stop: float | None
    data_download_status: str = "failed"
    market_rows: int = 0
    benchmark_rows: int = 0
    entry_candidates_found: int = 0
    open_positions_processed: int = 0
    exit_checks_processed: int = 0
    strategy_executed: bool = False
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated paper-trading runner for leadership_expansion_v1")
    parser.add_argument("--config", type=Path, default=Path("config") / "backtest_config.json")
    parser.add_argument("--tickers", type=str, help="Comma-separated ticker override")
    parser.add_argument("--lookback-days", type=int, default=420)
    parser.add_argument("--portfolio", type=Path, default=PORTFOLIO_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = DailyRunLogger()
    notifier = TelegramNotifier()
    errors: list[str] = []
    results: list[SymbolRunResult] = []

    try:
        checks = assert_startup_checks()
        logger.info("Startup checks passed", checks=[asdict(check) for check in checks])
    except Exception as exc:
        logger.error("Startup checks failed", error=str(exc))
        notify_safely(
            notifier,
            logger,
            "startup_checks",
            lambda: notifier.send_error(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                exception=str(exc),
                failed_component="startup_checks",
            ),
        )
        summary = logger.write_summary(
            success=False,
            signals_generated=0,
            open_positions=0,
            errors=[str(exc)],
            details={"closed_positions": 0},
        )
        return 1

    config = load_paper_config(args.config)
    tickers = resolve_universe(args.tickers)
    logger.info("Paper run started", strategy=STRATEGY_NAME, tickers=tickers, telegram_enabled=notifier.enabled)
    notify_safely(
        notifier,
        logger,
        "run_started",
        lambda: notifier.send_run_started(
            timestamp=logger.started_at.isoformat(timespec="seconds"),
            execution_time=logger.started_at.strftime("%H:%M:%S"),
            universe_size=len(tickers),
        ),
    )

    data_source = YahooFinanceDataSource()
    benchmark_data = fetch_benchmark_data(data_source, config, args.lookback_days, logger, errors)
    if benchmark_data is None:
        notify_safely(
            notifier,
            logger,
            "benchmark_data",
            lambda: notifier.send_error(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                exception="Benchmark market data unavailable",
                failed_component="benchmark_data",
            ),
        )

    for ticker in tickers:
        try:
            result = run_symbol(
                ticker=ticker,
                config=config,
                data_source=data_source,
                benchmark_data=benchmark_data,
                lookback_days=args.lookback_days,
            )
            results.append(result)
            logger.info(
                "Symbol processed",
                ticker=ticker,
                latest_date=result.latest_date,
                signals=len(result.signals),
                closed_trades=len(result.closed_trades),
            )
        except Exception as exc:
            message = f"{ticker}: {exc}"
            errors.append(message)
            results.append(
                SymbolRunResult(
                    ticker=ticker,
                    latest_date=None,
                    latest_close=None,
                    signals=[],
                    closed_trades=pd.DataFrame(),
                    open_stop=None,
                    data_download_status="failed",
                    error=message,
                )
            )
            logger.error("Symbol failed; continuing with remaining tickers", ticker=ticker, error=str(exc))
            notify_safely(
                notifier,
                logger,
                f"symbol:{ticker}",
                lambda exc=exc, ticker=ticker: notifier.send_error(
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                    exception=str(exc),
                    failed_component=f"symbol:{ticker}",
                ),
            )

    signals = [signal for result in results for signal in result.signals]
    report_path = write_daily_signal_report(signals)
    previous_closed_keys = closed_position_keys(read_portfolio(args.portfolio))
    portfolio = update_portfolio(args.portfolio, config, results, signals)
    open_positions = int((portfolio["status"] == "OPEN").sum()) if not portfolio.empty else 0
    open_positions_checked = open_positions
    newly_closed = find_newly_closed_positions(portfolio, previous_closed_keys)
    closed_positions = len(newly_closed)
    portfolio_equity = latest_portfolio_value(portfolio, "current_equity")
    current_drawdown = latest_portfolio_value(portfolio, "drawdown")

    for signal in signals:
        notify_safely(notifier, logger, f"signal:{signal.ticker}", lambda signal=signal: notifier.send_signal(signal))
    for _, closed_position in newly_closed.iterrows():
        notify_safely(
            notifier,
            logger,
            f"closed:{closed_position.get('ticker', '')}",
            lambda closed_position=closed_position: notifier.send_position_closed(
                ticker=str(closed_position.get("ticker", "")),
                exit_reason=str(closed_position.get("exit_reason", "")),
                entry_date=str(closed_position.get("entry_date", "")),
                exit_date=str(closed_position.get("exit_date", "")),
                r_multiple=str(closed_position.get("R_multiple", "")),
                pnl=str(closed_position.get("PnL", "")),
            ),
        )

    logger.info("Reports written", signal_report=str(report_path.resolve()), portfolio=str(args.portfolio.resolve()))
    run_status = "success" if not errors else "failure"
    summary = logger.write_summary(
        success=not errors,
        signals_generated=len(signals),
        open_positions=open_positions,
        errors=errors,
        details={
            "tickers_requested": len(tickers),
            "tickers_processed": len([result for result in results if result.error is None]),
            "closed_positions": closed_positions,
            "portfolio_equity": portfolio_equity,
            "current_drawdown": current_drawdown,
            "open_positions_checked": open_positions_checked,
            "signal_report": str(report_path.resolve()),
            "portfolio": str(args.portfolio.resolve()),
        },
    )
    verification = build_execution_verification(
        execution_timestamp=logger.started_at,
        strategy_name=STRATEGY_NAME,
        tickers=tickers,
        results=results,
        execution_duration_seconds=summary.execution_duration_seconds,
        open_positions_checked=open_positions_checked,
    )
    verification_path = write_execution_verification(verification)
    logger.info("Execution verification written", path=str(verification_path.resolve()))
    performance_record = append_daily_performance(
        execution_timestamp=logger.started_at,
        verification=verification,
        portfolio=portfolio,
        initial_equity=config.initial_capital,
        signals_generated=len(signals),
        open_positions=open_positions,
        closed_positions=closed_positions,
    )
    logger.info("Performance dashboard updated", performance=asdict(performance_record))
    data_loaded_count = sum(1 for status in verification.data_download_status_per_ticker.values() if status == "loaded")
    notify_safely(
        notifier,
        logger,
        "daily_summary",
        lambda: notifier.send_daily_summary(
            signals_generated=len(signals),
            open_positions=open_positions,
            closed_positions=closed_positions,
            portfolio_equity=portfolio_equity,
            current_drawdown=current_drawdown,
            run_status=run_status,
            tickers_scanned=verification.number_of_tickers_scanned,
            data_loaded=f"{data_loaded_count}/{verification.number_of_tickers_scanned}",
            candidates_found=verification.number_of_entry_candidates_found,
            open_positions_checked=verification.number_of_open_positions_processed,
            strategy_executed=verification.strategy_executed,
        ),
    )
    return 0 if not errors else 2


def load_paper_config(config_path: Path) -> BacktestConfig:
    config = load_config(config_path)
    config.strategy_name = STRATEGY_NAME
    config.timeframe = "1d"
    config.plot = False
    return config


def resolve_universe(tickers_arg: str | None) -> list[str]:
    explicit = tickers_arg or os.environ.get("PAPER_TICKERS")
    if explicit:
        return sorted({ticker.strip().upper() for ticker in explicit.split(",") if ticker.strip()})

    if PAPER_UNIVERSE_PATH.exists():
        universe = pd.read_csv(PAPER_UNIVERSE_PATH)
        if "ticker" in universe.columns and not universe.empty:
            return sorted(universe["ticker"].dropna().astype(str).str.upper().unique().tolist())

    if UNIVERSE_PATH.exists():
        universe = pd.read_csv(UNIVERSE_PATH)
        if "universe_name" in universe.columns:
            universe = universe[universe["universe_name"] == "ALL_ASSETS"]
        if "ticker" in universe.columns and not universe.empty:
            return sorted(universe["ticker"].dropna().astype(str).str.upper().unique().tolist())

    return ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]


def fetch_benchmark_data(
    data_source: YahooFinanceDataSource,
    config: BacktestConfig,
    lookback_days: int,
    logger: DailyRunLogger,
    errors: list[str],
) -> pd.DataFrame | None:
    try:
        return fetch_market_data(data_source, config.benchmark_ticker, lookback_days)
    except Exception as exc:
        message = f"benchmark {config.benchmark_ticker}: {exc}"
        errors.append(message)
        logger.error("Benchmark download failed; relative-strength scans cannot run", error=message)
        return None


def run_symbol(
    *,
    ticker: str,
    config: BacktestConfig,
    data_source: YahooFinanceDataSource,
    benchmark_data: pd.DataFrame | None,
    lookback_days: int,
) -> SymbolRunResult:
    if benchmark_data is None:
        raise RuntimeError("benchmark data unavailable")

    market_data = fetch_market_data(data_source, ticker, lookback_days)
    aligned_market, aligned_benchmark = align_market_and_benchmark(market_data, benchmark_data)
    strategy = run_strategy_probe(ticker, aligned_market, aligned_benchmark, config)
    latest_timestamp = aligned_market.index[-1]
    latest_date = latest_timestamp.date().isoformat()
    latest_close = float(aligned_market["Close"].iloc[-1])
    signals = extract_pending_signals(strategy, ticker, latest_date, config)
    closed_trades = strategy.trade_journal.to_dataframe()
    active_trade_count = len(getattr(strategy, "active_sizes", {}))
    return SymbolRunResult(
        ticker=ticker,
        latest_date=latest_date,
        latest_close=latest_close,
        signals=signals,
        closed_trades=closed_trades,
        open_stop=latest_open_stop(strategy),
        data_download_status="loaded",
        market_rows=len(aligned_market),
        benchmark_rows=len(aligned_benchmark),
        entry_candidates_found=len(signals),
        open_positions_processed=active_trade_count,
        exit_checks_processed=len(aligned_market),
        strategy_executed=True,
    )


def fetch_market_data(data_source: YahooFinanceDataSource, ticker: str, lookback_days: int) -> pd.DataFrame:
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=lookback_days)
    return data_source.fetch(
        MarketDataRequest(
            ticker=ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            timeframe="1d",
        )
    )


def align_market_and_benchmark(
    market_data: pd.DataFrame,
    benchmark_data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    common_index = market_data.index.intersection(benchmark_data.index)
    if len(common_index) < 260:
        raise ValueError(f"Not enough aligned daily bars: {len(common_index)}")
    return market_data.loc[common_index].copy(), benchmark_data.loc[common_index].copy()


def run_strategy_probe(
    ticker: str,
    market_data: pd.DataFrame,
    benchmark_data: pd.DataFrame,
    config: BacktestConfig,
) -> LeadershipExpansionV1Strategy:
    cerebro = bt.Cerebro(stdstats=False, cheat_on_open=False)
    cerebro.broker.setcash(config.initial_capital)
    cerebro.broker.setcommission(commission=config.commission)
    cerebro.broker.set_slippage_perc(config.slippage, slip_open=True, slip_limit=True, slip_match=True)
    cerebro.adddata(PandasOHLCVData(dataname=market_data), name=ticker)
    cerebro.adddata(PandasOHLCVData(dataname=benchmark_data), name=config.benchmark_ticker)
    config.skip_relative_strength_filter = ticker.upper() == config.benchmark_ticker.upper()
    cerebro.addstrategy(LeadershipExpansionV1Strategy, **build_strategy_params(config))
    strategies = cerebro.run()
    return strategies[0]


def extract_pending_signals(
    strategy: LeadershipExpansionV1Strategy,
    ticker: str,
    signal_date: str,
    config: BacktestConfig,
) -> list[SignalRecord]:
    signals: list[SignalRecord] = []
    for trade_id in getattr(strategy, "pending_entries", {}):
        stop_price = float(getattr(strategy, "planned_stops", {}).get(trade_id, 0.0))
        order = strategy.pending_entries[trade_id]
        size = int(abs(getattr(order.created, "size", 0) or 0))
        entry_price = float(getattr(order.created, "price", 0.0) or strategy.data_stock.close[0])
        signals.append(
            SignalRecord(
                date=signal_date,
                ticker=ticker,
                signal_type="BUY",
                entry_price=round(entry_price, 4),
                stop_price=round(stop_price, 4),
                risk_per_trade=config.risk_per_trade,
                position_size=size,
                strategy_name=STRATEGY_NAME,
            )
        )
    return signals


def latest_open_stop(strategy: LeadershipExpansionV1Strategy) -> float | None:
    stops = getattr(strategy, "current_stops", {})
    if not stops:
        return None
    return round(float(max(stops.values())), 4)


def update_portfolio(
    path: Path,
    config: BacktestConfig,
    results: list[SymbolRunResult],
    signals: list[SignalRecord],
) -> pd.DataFrame:
    portfolio = read_portfolio(path)
    today = date.today().isoformat()

    for result in results:
        if result.error is not None:
            continue
        portfolio = mark_closed_trades(portfolio, result, config)
        portfolio = refresh_open_marks(portfolio, result, today)

    for signal in signals:
        duplicate_open = (
            (portfolio["status"] == "OPEN")
            & (portfolio["ticker"] == signal.ticker)
            & (portfolio["entry_date"] == signal.date)
        )
        if duplicate_open.any():
            continue
        portfolio = pd.concat(
            [
                portfolio,
                pd.DataFrame(
                    [
                        {
                            "strategy_name": signal.strategy_name,
                            "ticker": signal.ticker,
                            "status": "OPEN",
                            "entry_date": signal.date,
                            "exit_date": "",
                            "entry_price": signal.entry_price,
                            "exit_price": "",
                            "stop_price": signal.stop_price,
                            "position_size": signal.position_size,
                            "risk_per_trade": signal.risk_per_trade,
                            "R_multiple": "",
                            "PnL": "",
                            "current_equity": "",
                            "drawdown": "",
                            "last_updated": today,
                            "exit_reason": "",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    portfolio = recompute_equity(portfolio, config.initial_capital)
    path.parent.mkdir(parents=True, exist_ok=True) if path.parent != Path(".") else None
    portfolio.to_csv(path, index=False)
    return portfolio


def read_portfolio(path: Path) -> pd.DataFrame:
    if path.exists():
        portfolio = pd.read_csv(path, dtype=object).fillna("")
        for column in PORTFOLIO_COLUMNS:
            if column not in portfolio.columns:
                portfolio[column] = ""
        return normalize_portfolio_frame(portfolio)
    return normalize_portfolio_frame(pd.DataFrame(columns=PORTFOLIO_COLUMNS))


def normalize_portfolio_frame(portfolio: pd.DataFrame) -> pd.DataFrame:
    for column in PORTFOLIO_COLUMNS:
        if column not in portfolio.columns:
            portfolio[column] = ""
    return portfolio[PORTFOLIO_COLUMNS].astype(object)


def closed_position_keys(portfolio: pd.DataFrame) -> set[tuple[str, str, str]]:
    if portfolio.empty:
        return set()
    closed = portfolio[portfolio["status"] == "CLOSED"]
    return {
        (str(row.get("ticker", "")), str(row.get("entry_date", "")), str(row.get("exit_date", "")))
        for _, row in closed.iterrows()
    }


def find_newly_closed_positions(
    portfolio: pd.DataFrame,
    previous_closed_keys: set[tuple[str, str, str]],
) -> pd.DataFrame:
    if portfolio.empty:
        return pd.DataFrame(columns=PORTFOLIO_COLUMNS)
    closed = portfolio[portfolio["status"] == "CLOSED"].copy()
    if closed.empty:
        return closed
    mask = [
        (str(row.get("ticker", "")), str(row.get("entry_date", "")), str(row.get("exit_date", "")))
        not in previous_closed_keys
        for _, row in closed.iterrows()
    ]
    return closed[mask]


def latest_portfolio_value(portfolio: pd.DataFrame, column: str) -> str:
    if portfolio.empty or column not in portfolio.columns:
        return ""
    values = portfolio[column].replace("", pd.NA).dropna()
    if values.empty:
        return ""
    return str(values.iloc[-1])


def notify_safely(
    notifier: TelegramNotifier,
    logger: DailyRunLogger,
    component: str,
    send_callback: Any,
) -> None:
    try:
        sent = send_callback()
        if sent:
            logger.info("Telegram notification sent", component=component)
        else:
            logger.info("Telegram notification skipped", component=component, enabled=notifier.enabled)
    except Exception as exc:
        logger.warning("Telegram notification failed", component=component, error=str(exc))


def mark_closed_trades(
    portfolio: pd.DataFrame,
    result: SymbolRunResult,
    config: BacktestConfig,
) -> pd.DataFrame:
    if result.closed_trades.empty:
        return portfolio

    closed = result.closed_trades.copy()
    if "entry_time" not in closed.columns or "exit_time" not in closed.columns:
        return portfolio

    for _, trade in closed.iterrows():
        entry_date = normalize_date(trade.get("entry_time"))
        exit_date = normalize_date(trade.get("exit_time"))
        if not entry_date or not exit_date:
            continue

        match = (
            (portfolio["ticker"] == result.ticker)
            & (portfolio["entry_date"] == entry_date)
            & (portfolio["status"] == "OPEN")
        )
        if not match.any():
            open_for_ticker = (portfolio["ticker"] == result.ticker) & (portfolio["status"] == "OPEN")
            open_indexes = portfolio[open_for_ticker].index.tolist()
            if len(open_indexes) == 1:
                match = portfolio.index == open_indexes[0]
        if not match.any():
            continue

        index = portfolio[match].index[0]
        portfolio.loc[index, "status"] = "CLOSED"
        portfolio.loc[index, "exit_date"] = exit_date
        portfolio.loc[index, "exit_price"] = safe_float(trade.get("exit_price"))
        portfolio.loc[index, "R_multiple"] = safe_float(trade.get("R_multiple"))
        portfolio.loc[index, "PnL"] = safe_float(trade.get("pnl_dollars"))
        portfolio.loc[index, "last_updated"] = date.today().isoformat()
        portfolio.loc[index, "exit_reason"] = str(trade.get("exit_reason", ""))
        if not portfolio.loc[index, "risk_per_trade"]:
            portfolio.loc[index, "risk_per_trade"] = config.risk_per_trade

    return portfolio


def refresh_open_marks(portfolio: pd.DataFrame, result: SymbolRunResult, today: str) -> pd.DataFrame:
    if result.latest_close is None:
        return portfolio
    match = (portfolio["ticker"] == result.ticker) & (portfolio["status"] == "OPEN")
    for index in portfolio[match].index:
        entry_price = to_float(portfolio.loc[index, "entry_price"])
        position_size = to_float(portfolio.loc[index, "position_size"])
        if entry_price is None or position_size is None:
            continue
        portfolio.loc[index, "PnL"] = round((result.latest_close - entry_price) * position_size, 4)
        if result.open_stop is not None:
            portfolio.loc[index, "stop_price"] = result.open_stop
        portfolio.loc[index, "last_updated"] = today
    return portfolio


def recompute_equity(portfolio: pd.DataFrame, initial_equity: float) -> pd.DataFrame:
    if portfolio.empty:
        return portfolio
    portfolio = normalize_portfolio_frame(portfolio)
    running_equity = initial_equity
    peak_equity = initial_equity
    for index in portfolio.index:
        pnl = to_float(portfolio.loc[index, "PnL"]) or 0.0
        if portfolio.loc[index, "status"] == "CLOSED":
            running_equity += pnl
        marked_equity = running_equity + (pnl if portfolio.loc[index, "status"] == "OPEN" else 0.0)
        peak_equity = max(peak_equity, marked_equity)
        drawdown = (marked_equity - peak_equity) / peak_equity if peak_equity > 0 else 0.0
        portfolio.loc[index, "current_equity"] = round(marked_equity, 4)
        portfolio.loc[index, "drawdown"] = round(drawdown, 6)
    return portfolio


def normalize_date(value: Any) -> str:
    if value is None or str(value) == "NaT":
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def safe_float(value: Any) -> str:
    parsed = to_float(value)
    return "" if parsed is None else str(round(parsed, 6))


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
