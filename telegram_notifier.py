from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi

REPO_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REPO_ROOT / "config" / "telegram_config.json"


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

    # Legacy leadership_expansion_v1 methods (preserved for backwards compatibility)
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
                    f"Ticker: {getattr(signal, 'ticker', '')}",
                    f"Entry Price: {getattr(signal, 'entry_price', '')}",
                    f"Stop Price: {getattr(signal, 'stop_price', '')}",
                    f"Risk %: {float(getattr(signal, 'risk_per_trade', 0.0)) * 100:.2f}",
                    f"Position Size: {getattr(signal, 'position_size', '')}",
                    f"Strategy: {getattr(signal, 'strategy_name', '')}",
                    f"Date: {getattr(signal, 'date', '')}",
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

    # --- New CSM-001 x TSM-001 Monthly Paper Strategy Notifications ---
    def send_csm_tsm_daily_status(
        self,
        *,
        account_equity: float,
        cash: float,
        positions_count: int,
        open_orders_count: int,
        system_state: str,
        controller_state: str,
        rebalance_due: bool,
        next_signal: str,
        earliest_execution: str,
        action_today: str = "NONE",
    ) -> bool:
        lines = [
            "CSM×TSM PAPER STATUS",
            "",
            f"Account equity: ${account_equity:,.2f}",
            f"Cash: ${cash:,.2f}",
            "",
            f"Positions: {positions_count}",
            f"Open orders: {open_orders_count}",
            "",
            "System:",
            f"{system_state}",
            "",
            "State:",
            f"{controller_state}",
            "",
            "Rebalance due:",
            "YES" if rebalance_due else "NO",
            "",
            "Next signal:",
            f"{next_signal}",
            "",
            "Earliest execution:",
            f"{earliest_execution}",
            "",
            "Action today:",
            f"{action_today}",
        ]
        return self.send("\n".join(lines))

    def send_csm_tsm_monthly_signal(
        self,
        *,
        signal_session: str,
        eligible_count: int,
        csm_candidates: int,
        tsm_approved: int,
        target_holdings: int,
        target_weight: float,
        identity_state: str,
        data_state: str,
        earliest_execution: str,
        orders_submitted: int = 0,
        status: str = "SIGNAL_READY_WAITING_FOR_T+1",
    ) -> bool:
        lines = [
            "CSM×TSM MONTHLY SIGNAL",
            "",
            "Signal session:",
            f"{signal_session}",
            "",
            "Eligible securities:",
            f"{eligible_count}",
            "",
            "CSM candidates:",
            f"{csm_candidates}",
            "",
            "TSM approved:",
            f"{tsm_approved}",
            "",
            "Target holdings:",
            f"{target_holdings}",
            "",
            "Target weight:",
            f"{target_weight:.2f}",
            "",
            "Identity:",
            f"{identity_state}",
            "",
            "Data:",
            f"{data_state}",
            "",
            "Earliest execution:",
            f"{earliest_execution}",
            "",
            "Orders submitted:",
            f"{orders_submitted}",
            "",
            "Status:",
            f"{status}",
        ]
        return self.send("\n".join(lines))

    def send_csm_tsm_execution_report(
        self,
        *,
        buys: int,
        sells: int,
        open_orders: int,
        positions: int,
        account_equity: float,
        execution_state: str,
    ) -> bool:
        lines = [
            "PAPER REBALANCE EXECUTION",
            "",
            "Buys:",
            f"{buys}",
            "",
            "Sells:",
            f"{sells}",
            "",
            "Open orders:",
            f"{open_orders}",
            "",
            "Positions:",
            f"{positions}",
            "",
            "Account equity:",
            f"${account_equity:,.2f}",
            "",
            "Execution state:",
            f"{execution_state}",
        ]
        return self.send("\n".join(lines))

    def send_csm_tsm_block_alert(
        self,
        *,
        alert_type: str,
        state: str,
        block_reason: str,
        incidents: list[str],
    ) -> bool:
        lines = [
            "CSM×TSM PAPER ALERT",
            "",
            "Alert type:",
            f"{alert_type}",
            "",
            "State:",
            f"{state}",
            "",
            "Block reason:",
            f"{block_reason}",
            "",
            "Incidents:",
            ", ".join(incidents) if incidents else "NONE",
            "",
            "Action taken:",
            "BLOCK (Zero orders submitted)",
        ]
        return self.send("\n".join(lines))

    def send_csm_tsm_migration_test(self) -> bool:
        lines = [
            "CSM×TSM PAPER SYSTEM",
            "",
            "Telegram migration test: PASS",
            "",
            "Environment: PAPER",
            "Trading enabled: NO",
            "Paper execution enabled: NO",
            "Orders submitted: 0",
            "",
            "State:",
            "WAITING_FOR_SCHEDULED_REBALANCE",
            "",
            "This is a status notification only.",
        ]
        return self.send("\n".join(lines))

    def send(self, message: str) -> bool:
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
        payload = urlencode({"chat_id": self.config.chat_id, "text": message}).encode("utf-8")
        request = Request(url, data=payload, method="POST")
        try:
            with urlopen(request, timeout=10, context=telegram_ssl_context()) as response:
                return 200 <= response.status < 300
        except Exception:
            return False

    @staticmethod
    def _load_config(config_path: Path) -> TelegramConfig:
        if not config_path.exists():
            return TelegramConfig()
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            return TelegramConfig(
                bot_token=str(payload.get("bot_token", "")),
                chat_id=str(payload.get("chat_id", "")),
                enabled=bool(payload.get("enabled", False)),
            )
        except Exception:
            return TelegramConfig()


def telegram_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())
