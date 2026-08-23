from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import argparse
import json


EXECUTION_VERIFICATION_PATH = Path("daily_logs") / "execution_verification.json"


@dataclass(slots=True)
class TickerExecutionVerification:
    ticker: str
    data_download_status: str
    market_rows: int
    benchmark_rows: int
    latest_date: str
    entry_candidates_found: int
    open_positions_processed: int
    exit_checks_processed: int
    strategy_executed: bool
    error: str


@dataclass(slots=True)
class StrategyExecutionVerification:
    execution_timestamp: str
    strategy_name: str
    number_of_tickers_scanned: int
    tickers_scanned: list[str]
    data_download_status_per_ticker: dict[str, str]
    number_of_entry_candidates_found: int
    number_of_open_positions_processed: int
    number_of_exit_checks_processed: int
    execution_duration_seconds: float
    strategy_executed: str
    ticker_details: list[TickerExecutionVerification]


def build_execution_verification(
    *,
    execution_timestamp: datetime,
    strategy_name: str,
    tickers: list[str],
    results: list[Any],
    execution_duration_seconds: float,
    open_positions_checked: int,
) -> StrategyExecutionVerification:
    details: list[TickerExecutionVerification] = []
    for result in results:
        details.append(
            TickerExecutionVerification(
                ticker=str(result.ticker),
                data_download_status=str(getattr(result, "data_download_status", "failed")),
                market_rows=int(getattr(result, "market_rows", 0)),
                benchmark_rows=int(getattr(result, "benchmark_rows", 0)),
                latest_date=str(result.latest_date or ""),
                entry_candidates_found=int(getattr(result, "entry_candidates_found", len(result.signals))),
                open_positions_processed=int(getattr(result, "open_positions_processed", 0)),
                exit_checks_processed=int(getattr(result, "exit_checks_processed", 0)),
                strategy_executed=bool(getattr(result, "strategy_executed", False)),
                error=str(result.error or ""),
            )
        )

    return StrategyExecutionVerification(
        execution_timestamp=execution_timestamp.isoformat(timespec="seconds"),
        strategy_name=strategy_name,
        number_of_tickers_scanned=len(tickers),
        tickers_scanned=tickers,
        data_download_status_per_ticker={detail.ticker: detail.data_download_status for detail in details},
        number_of_entry_candidates_found=sum(detail.entry_candidates_found for detail in details),
        number_of_open_positions_processed=open_positions_checked,
        number_of_exit_checks_processed=sum(detail.exit_checks_processed for detail in details),
        execution_duration_seconds=round(execution_duration_seconds, 3),
        strategy_executed="YES" if any(detail.strategy_executed for detail in details) else "NO",
        ticker_details=details,
    )


def write_execution_verification(
    verification: StrategyExecutionVerification,
    output_path: Path = EXECUTION_VERIFICATION_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(verification), indent=2), encoding="utf-8")
    return output_path


def load_execution_verification(path: Path = EXECUTION_VERIFICATION_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate latest strategy execution verification artifact")
    parser.add_argument("--path", type=Path, default=EXECUTION_VERIFICATION_PATH)
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Missing execution verification file: {args.path}")
        return 1

    payload = load_execution_verification(args.path)
    required_fields = [
        "execution_timestamp",
        "strategy_name",
        "number_of_tickers_scanned",
        "tickers_scanned",
        "data_download_status_per_ticker",
        "number_of_entry_candidates_found",
        "number_of_open_positions_processed",
        "number_of_exit_checks_processed",
        "execution_duration_seconds",
        "strategy_executed",
    ]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        print(f"Execution verification missing fields: {missing}")
        return 1
    if payload.get("strategy_executed") != "YES":
        print("Strategy Executed: NO")
        return 1

    print("Strategy Executed: YES")
    print(f"Tickers Scanned: {payload['number_of_tickers_scanned']}")
    print(f"Candidates Found: {payload['number_of_entry_candidates_found']}")
    print(f"Open Positions Checked: {payload['number_of_open_positions_processed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
