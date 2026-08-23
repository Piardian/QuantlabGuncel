from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import argparse
import html

import pandas as pd

from config.settings import BacktestConfig
from verify_strategy_execution import StrategyExecutionVerification, load_execution_verification


PERFORMANCE_HISTORY_PATH = Path("daily_logs") / "paper_performance_history.csv"
PERFORMANCE_DASHBOARD_PATH = Path("daily_logs") / "paper_performance_dashboard.html"


@dataclass(slots=True)
class DailyPerformanceRecord:
    run_date: str
    execution_timestamp: str
    runs_executed: int
    candidates_found: int
    signals_generated: int
    open_positions: int
    closed_positions: int
    portfolio_equity: float
    cumulative_R: float
    win_rate: float
    average_R: float
    max_drawdown: float


def append_daily_performance(
    *,
    execution_timestamp: datetime,
    verification: StrategyExecutionVerification,
    portfolio: pd.DataFrame,
    initial_equity: float,
    signals_generated: int,
    open_positions: int,
    closed_positions: int,
    history_path: Path = PERFORMANCE_HISTORY_PATH,
    dashboard_path: Path = PERFORMANCE_DASHBOARD_PATH,
) -> DailyPerformanceRecord:
    history = read_history(history_path)
    run_date = execution_timestamp.date().isoformat()
    runs_executed = int((history["run_date"] == run_date).sum()) + 1 if not history.empty else 1
    metrics = build_portfolio_metrics(portfolio=portfolio, initial_equity=initial_equity)
    record = DailyPerformanceRecord(
        run_date=run_date,
        execution_timestamp=execution_timestamp.isoformat(timespec="seconds"),
        runs_executed=runs_executed,
        candidates_found=verification.number_of_entry_candidates_found,
        signals_generated=signals_generated,
        open_positions=open_positions,
        closed_positions=closed_positions,
        portfolio_equity=metrics["portfolio_equity"],
        cumulative_R=metrics["cumulative_R"],
        win_rate=metrics["win_rate"],
        average_R=metrics["average_R"],
        max_drawdown=metrics["max_drawdown"],
    )

    updated_history = pd.concat([history, pd.DataFrame([asdict(record)])], ignore_index=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    updated_history.to_csv(history_path, index=False)
    write_dashboard(updated_history, dashboard_path)
    return record


def build_portfolio_metrics(portfolio: pd.DataFrame, initial_equity: float) -> dict[str, float]:
    if portfolio.empty:
        return {
            "portfolio_equity": round(initial_equity, 4),
            "cumulative_R": 0.0,
            "win_rate": 0.0,
            "average_R": 0.0,
            "max_drawdown": 0.0,
        }

    closed = portfolio[portfolio["status"] == "CLOSED"].copy() if "status" in portfolio.columns else pd.DataFrame()
    r_values = pd.to_numeric(closed.get("R_multiple", pd.Series(dtype=float)), errors="coerce").dropna()
    drawdowns = pd.to_numeric(portfolio.get("drawdown", pd.Series(dtype=float)), errors="coerce").dropna()
    equity_values = pd.to_numeric(portfolio.get("current_equity", pd.Series(dtype=float)), errors="coerce").dropna()

    cumulative_r = float(r_values.sum()) if not r_values.empty else 0.0
    average_r = float(r_values.mean()) if not r_values.empty else 0.0
    win_rate = float((r_values > 0).sum() / len(r_values) * 100.0) if len(r_values) else 0.0
    max_drawdown = float(drawdowns.min()) if not drawdowns.empty else 0.0
    portfolio_equity = float(equity_values.iloc[-1]) if not equity_values.empty else initial_equity

    return {
        "portfolio_equity": round(portfolio_equity, 4),
        "cumulative_R": round(cumulative_r, 6),
        "win_rate": round(win_rate, 4),
        "average_R": round(average_r, 6),
        "max_drawdown": round(max_drawdown, 6),
    }


def read_history(path: Path = PERFORMANCE_HISTORY_PATH) -> pd.DataFrame:
    columns = [field_name for field_name in DailyPerformanceRecord.__dataclass_fields__]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    history = pd.read_csv(path)
    for column in columns:
        if column not in history.columns:
            history[column] = ""
    return history[columns]


def write_dashboard(history: pd.DataFrame, path: Path = PERFORMANCE_DASHBOARD_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    latest = history.iloc[-1].to_dict() if not history.empty else {}
    html_text = build_dashboard_html(history, latest)
    path.write_text(html_text, encoding="utf-8")
    return path


def build_dashboard_html(history: pd.DataFrame, latest: dict[str, Any]) -> str:
    cards = [
        ("Runs Today", latest.get("runs_executed", "")),
        ("Candidates", latest.get("candidates_found", "")),
        ("Signals", latest.get("signals_generated", "")),
        ("Open Positions", latest.get("open_positions", "")),
        ("Closed Positions", latest.get("closed_positions", "")),
        ("Portfolio Equity", latest.get("portfolio_equity", "")),
        ("Cumulative R", latest.get("cumulative_R", "")),
        ("Win Rate", latest.get("win_rate", "")),
        ("Average R", latest.get("average_R", "")),
        ("Max Drawdown", latest.get("max_drawdown", "")),
    ]
    card_html = "\n".join(
        f'<section class="metric"><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></section>'
        for label, value in cards
    )
    table_html = history.tail(60).to_html(index=False, escape=True, classes="history-table")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Trading Performance Dashboard</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f6f7f9;
      color: #1f2933;
    }}
    header {{
      padding: 24px 32px 12px;
      background: #ffffff;
      border-bottom: 1px solid #d8dee6;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      font-weight: 700;
    }}
    .timestamp {{
      margin-top: 6px;
      color: #64748b;
      font-size: 13px;
    }}
    main {{
      padding: 24px 32px 40px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .metric {{
      background: #ffffff;
      border: 1px solid #d8dee6;
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .metric span {{
      display: block;
      color: #64748b;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .metric strong {{
      font-size: 20px;
      line-height: 1.2;
    }}
    .table-wrap {{
      overflow-x: auto;
      background: #ffffff;
      border: 1px solid #d8dee6;
      border-radius: 8px;
      padding: 12px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid #e5e9ef;
      padding: 8px 10px;
      text-align: right;
      white-space: nowrap;
    }}
    th:first-child, td:first-child,
    th:nth-child(2), td:nth-child(2) {{
      text-align: left;
    }}
    th {{
      background: #f1f4f8;
      color: #334155;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Paper Trading Performance Dashboard</h1>
    <div class="timestamp">Last updated: {html.escape(str(latest.get("execution_timestamp", "")))}</div>
  </header>
  <main>
    <section class="metrics">
      {card_html}
    </section>
    <section class="table-wrap">
      {table_html}
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build paper trading performance dashboard from latest artifacts")
    parser.add_argument("--portfolio", type=Path, default=Path("paper_portfolio.csv"))
    parser.add_argument("--initial-equity", type=float, default=BacktestConfig().initial_capital)
    args = parser.parse_args()

    verification_payload = load_execution_verification()
    portfolio = pd.read_csv(args.portfolio, dtype=str).fillna("") if args.portfolio.exists() else pd.DataFrame()
    record = append_daily_performance(
        execution_timestamp=pd.to_datetime(verification_payload["execution_timestamp"]).to_pydatetime(),
        verification=StrategyExecutionVerification(
            execution_timestamp=verification_payload["execution_timestamp"],
            strategy_name=verification_payload["strategy_name"],
            number_of_tickers_scanned=int(verification_payload["number_of_tickers_scanned"]),
            tickers_scanned=list(verification_payload["tickers_scanned"]),
            data_download_status_per_ticker=dict(verification_payload["data_download_status_per_ticker"]),
            number_of_entry_candidates_found=int(verification_payload["number_of_entry_candidates_found"]),
            number_of_open_positions_processed=int(verification_payload["number_of_open_positions_processed"]),
            number_of_exit_checks_processed=int(verification_payload["number_of_exit_checks_processed"]),
            execution_duration_seconds=float(verification_payload["execution_duration_seconds"]),
            strategy_executed=str(verification_payload["strategy_executed"]),
            ticker_details=[],
        ),
        portfolio=portfolio,
        initial_equity=args.initial_equity,
        signals_generated=0,
        open_positions=int((portfolio.get("status", pd.Series(dtype=str)) == "OPEN").sum()) if not portfolio.empty else 0,
        closed_positions=0,
    )
    print(f"Dashboard updated: {PERFORMANCE_DASHBOARD_PATH}")
    print(f"History appended: {PERFORMANCE_HISTORY_PATH}")
    print(asdict(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
