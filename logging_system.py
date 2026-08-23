from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import json
import logging


LOG_DIR = Path("daily_logs")
LATEST_SUMMARY_PATH = LOG_DIR / "latest_run_summary.txt"


@dataclass(slots=True)
class RunSummary:
    timestamp: str
    status: str
    signals_generated: int
    open_positions: int
    errors: list[str]
    execution_duration_seconds: float
    details: dict[str, Any] = field(default_factory=dict)


class DailyRunLogger:
    def __init__(self, log_dir: Path = LOG_DIR) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.started_at = datetime.now()
        self.started_perf = perf_counter()
        stamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        self.text_log_path = self.log_dir / f"paper_trading_{stamp}.log"
        self.summary_path = self.log_dir / f"paper_trading_{stamp}.json"
        self.logger = logging.getLogger(f"paper_trading.{stamp}")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler = logging.FileHandler(self.text_log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str, **extra: Any) -> None:
        self.logger.info(self._format(message, extra))

    def warning(self, message: str, **extra: Any) -> None:
        self.logger.warning(self._format(message, extra))

    def error(self, message: str, **extra: Any) -> None:
        self.logger.error(self._format(message, extra))

    def write_summary(
        self,
        *,
        success: bool,
        signals_generated: int,
        open_positions: int,
        errors: list[str],
        details: dict[str, Any] | None = None,
    ) -> RunSummary:
        duration = perf_counter() - self.started_perf
        summary = RunSummary(
            timestamp=self.started_at.isoformat(timespec="seconds"),
            status="success" if success else "failure",
            signals_generated=signals_generated,
            open_positions=open_positions,
            errors=errors,
            execution_duration_seconds=round(duration, 3),
            details=details or {},
        )
        self.summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        self._write_latest_text_summary(summary)
        self.info(
            "Run finished",
            status=summary.status,
            signals_generated=signals_generated,
            open_positions=open_positions,
            error_count=len(errors),
            duration_seconds=summary.execution_duration_seconds,
        )
        return summary

    def _write_latest_text_summary(self, summary: RunSummary) -> None:
        closed_positions = summary.details.get("closed_positions", 0)
        lines = [
            f"Timestamp: {summary.timestamp}",
            f"Run Status: {summary.status}",
            f"Signals Generated: {summary.signals_generated}",
            f"Open Positions: {summary.open_positions}",
            f"Closed Positions: {closed_positions}",
            f"Execution Duration: {summary.execution_duration_seconds} seconds",
            "Errors:",
        ]
        if summary.errors:
            lines.extend(f"- {error}" for error in summary.errors)
        else:
            lines.append("- None")
        LATEST_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _format(message: str, extra: dict[str, Any]) -> str:
        if not extra:
            return message
        return f"{message} | {json.dumps(extra, sort_keys=True, default=str)}"
