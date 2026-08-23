from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import json
import ssl

import certifi


CONFIG_PATH = Path("config") / "telegram_config.json"


@dataclass(slots=True)
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = False


class TelegramNotifier:
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path
        self.config = self._load_config(config_path)

    @property
    def enabled(self) -> bool:
        return bool(self.config.enabled and self.config.bot_token and self.config.chat_id)

    def send_run_started(self, *, timestamp: str, execution_time: str, universe_size: int) -> bool:
        return self.send(
            "\n".join(
                [
                    "Paper Trading Run Started",
                    f"Timestamp: {timestamp}",
                    f"Execution Time: {execution_time}",
                    f"Universe Size: {universe_size}",
                ]
            )
        )

    def send_signal(self, signal: Any) -> bool:
        return self.send(
            "\n".join(
                [
                    "BUY SIGNAL",
                    f"Ticker: {signal.ticker}",
                    f"Entry Price: {signal.entry_price}",
                    f"Stop Price: {signal.stop_price}",
                    f"Risk %: {float(signal.risk_per_trade) * 100:.2f}",
                    f"Position Size: {signal.position_size}",
                    f"Strategy: {signal.strategy_name}",
                    f"Date: {signal.date}",
                ]
            )
        )

    def send_position_closed(self, *, ticker: str, exit_reason: str, entry_date: str, exit_date: str, r_multiple: str, pnl: str) -> bool:
        return self.send(
            "\n".join(
                [
                    "POSITION CLOSED",
                    f"Ticker: {ticker}",
                    f"Exit Reason: {exit_reason}",
                    f"Entry Date: {entry_date}",
                    f"Exit Date: {exit_date}",
                    f"R Multiple: {r_multiple}",
                    f"PnL: {pnl}",
                ]
            )
        )

    def send_daily_summary(
        self,
        *,
        signals_generated: int,
        open_positions: int,
        closed_positions: int,
        portfolio_equity: str,
        current_drawdown: str,
        run_status: str,
        tickers_scanned: int,
        data_loaded: str,
        candidates_found: int,
        open_positions_checked: int,
        strategy_executed: str,
    ) -> bool:
        return self.send(
            "\n".join(
                [
                    "DAILY SUMMARY",
                    f"Signals Generated: {signals_generated}",
                    f"Open Positions: {open_positions}",
                    f"Closed Positions: {closed_positions}",
                    f"Portfolio Equity: {portfolio_equity}",
                    f"Current Drawdown: {current_drawdown}",
                    f"Tickers Scanned: {tickers_scanned}",
                    f"Data Loaded: {data_loaded}",
                    f"Candidates Found: {candidates_found}",
                    f"Open Positions Checked: {open_positions_checked}",
                    f"Strategy Executed: {strategy_executed}",
                    f"Run Status: {run_status}",
                ]
            )
        )

    def send_error(self, *, timestamp: str, exception: str, failed_component: str) -> bool:
        return self.send(
            "\n".join(
                [
                    "ERROR",
                    f"Timestamp: {timestamp}",
                    f"Exception: {exception}",
                    f"Failed Component: {failed_component}",
                ]
            )
        )

    def send(self, message: str) -> bool:
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
        payload = urlencode({"chat_id": self.config.chat_id, "text": message}).encode("utf-8")
        request = Request(url, data=payload, method="POST")
        with urlopen(request, timeout=10, context=telegram_ssl_context()) as response:
            return 200 <= response.status < 300

    @staticmethod
    def _load_config(config_path: Path) -> TelegramConfig:
        if not config_path.exists():
            return TelegramConfig()
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        return TelegramConfig(
            bot_token=str(payload.get("bot_token", "")),
            chat_id=str(payload.get("chat_id", "")),
            enabled=bool(payload.get("enabled", False)),
        )


def telegram_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())
