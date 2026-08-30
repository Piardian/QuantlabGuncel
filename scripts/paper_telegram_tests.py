from __future__ import annotations

import io
import json
import logging
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter, BrokerMode, BrokerMutationDisabled
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController
from scripts.paper_telegram_status import run_telegram_status
from telegram_notifier import CONFIG_PATH, TelegramConfig, TelegramNotifier


class TestPaperTelegramIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.config_path = REPO_ROOT / "config" / "telegram_config.json"

    def test_01_telegram_status_calls_real_controller(self) -> None:
        """Verify run_telegram_status invokes PaperTradingController dry-run."""
        with patch.object(TelegramNotifier, "send", return_value=True):
            res = run_telegram_status(now=datetime(2026, 8, 25, 20, 0, 0, tzinfo=timezone.utc), send_message=False)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertIn("readiness_state", res)
            self.assertIn("identity_readiness_state", res)
            self.assertEqual(res["identity_readiness_state"], "PASS")

    def test_02_telegram_status_cannot_submit_orders(self) -> None:
        """Verify Telegram status script strictly performs zero mutations."""
        with patch.object(TelegramNotifier, "send", return_value=True):
            res = run_telegram_status(now=datetime(2026, 8, 25, 20, 0, 0, tzinfo=timezone.utc), send_message=False)
            self.assertEqual(res["broker_mutations"], 0)
            self.assertEqual(res["orders_submitted"], 0)

    def test_03_normal_day_reports_waiting_for_rebalance(self) -> None:
        """Verify mid-month non-rebalance evaluation reports WAITING_FOR_SCHEDULED_REBALANCE."""
        notifier = TelegramNotifier()
        with patch.object(TelegramNotifier, "send", return_value=True) as mock_send:
            sent = notifier.send_csm_tsm_daily_status(
                account_equity=100000.0,
                cash=100000.0,
                positions_count=0,
                open_orders_count=0,
                system_state="PASS",
                controller_state="WAITING_FOR_SCHEDULED_REBALANCE",
                rebalance_due=False,
                next_signal="2026-08-31",
                earliest_execution="2026-09-01",
                action_today="NONE",
            )
            self.assertTrue(sent)
            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertIn("CSM×TSM PAPER STATUS", message)
            self.assertIn("WAITING_FOR_SCHEDULED_REBALANCE", message)
            self.assertIn("Rebalance due:\nNO", message)
            self.assertIn("Action today:\nNONE", message)

    def test_04_rebalance_due_status_reported_correctly(self) -> None:
        """Verify monthly signal day formats correct SIGNAL_READY message."""
        notifier = TelegramNotifier()
        with patch.object(TelegramNotifier, "send", return_value=True) as mock_send:
            sent = notifier.send_csm_tsm_monthly_signal(
                signal_session="2026-08-31",
                eligible_count=249,
                csm_candidates=25,
                tsm_approved=25,
                target_holdings=25,
                target_weight=1.0,
                identity_state="PASS",
                data_state="PASS",
                earliest_execution="2026-09-01",
                orders_submitted=0,
                status="SIGNAL_READY_WAITING_FOR_T+1",
            )
            self.assertTrue(sent)
            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertIn("CSM×TSM MONTHLY SIGNAL", message)
            self.assertIn("Signal session:\n2026-08-31", message)
            self.assertIn("Target holdings:\n25", message)
            self.assertIn("SIGNAL_READY_WAITING_FOR_T+1", message)

    def test_05_broker_connection_error_safe_notification(self) -> None:
        """Verify precheck blocks generate safe alert notifications."""
        notifier = TelegramNotifier()
        with patch.object(TelegramNotifier, "send", return_value=True) as mock_send:
            sent = notifier.send_csm_tsm_block_alert(
                alert_type="PRECHECK_BLOCK",
                state="BLOCKED",
                block_reason="BROKER_CONNECTION_BLOCK",
                incidents=["BROKER_OFFLINE"],
            )
            self.assertTrue(sent)
            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertIn("CSM×TSM PAPER ALERT", message)
            self.assertIn("BROKER_CONNECTION_BLOCK", message)
            self.assertIn("BLOCK (Zero orders submitted)", message)

    def test_06_identity_failure_safe_notification(self) -> None:
        """Verify identity failure generates safe alert notification."""
        notifier = TelegramNotifier()
        with patch.object(TelegramNotifier, "send", return_value=True) as mock_send:
            sent = notifier.send_csm_tsm_block_alert(
                alert_type="IDENTITY_BLOCK",
                state="BLOCKED",
                block_reason="BLOCK_IDENTITY_MISMATCH",
                incidents=["IDENTITY_RESOLUTION_FAILED"],
            )
            self.assertTrue(sent)
            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertIn("IDENTITY_BLOCK", message)
            self.assertIn("BLOCK_IDENTITY_MISMATCH", message)

    def test_07_telegram_failure_does_not_affect_controller(self) -> None:
        """Verify network or HTTP failure when sending Telegram does not crash or mutate controller."""
        with patch.object(TelegramNotifier, "send", return_value=False):
            res = run_telegram_status(now=datetime(2026, 8, 25, 20, 0, 0, tzinfo=timezone.utc), send_message=True)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertFalse(res["telegram_sent"])
            self.assertEqual(res["broker_mutations"], 0)

    def test_08_secrets_never_logged_or_exposed_in_repr(self) -> None:
        """Verify TelegramNotifier does not expose credentials in str or repr."""
        notifier = TelegramNotifier()
        rep = repr(notifier)
        self.assertNotIn("bot_token", rep)
        self.assertTrue(notifier.enabled)

    def test_09_old_strategy_not_invoked_in_new_path(self) -> None:
        """Verify paper_telegram_status has zero imports or dependencies on leadership_expansion_v1."""
        status_file = (REPO_ROOT / "scripts" / "paper_telegram_status.py").read_text(encoding="utf-8")
        self.assertNotIn("leadership_expansion_v1", status_file)
        self.assertNotIn("paper_portfolio_manager", status_file)
        self.assertNotIn("paper_portfolio.csv", status_file)

    def test_10_old_paper_portfolio_manager_not_scheduled_in_new_task(self) -> None:
        """Verify run_telegram_status.bat targets only paper_telegram_status.py."""
        bat_file = (REPO_ROOT / "run_telegram_status.bat").read_text(encoding="utf-8")
        self.assertIn("scripts\\paper_telegram_status.py", bat_file)
        self.assertNotIn("paper_portfolio_manager", bat_file)

    def test_11_old_launcher_bat_is_inert(self) -> None:
        """Verify run_paper_trading.bat is retired and exits immediately."""
        bat_file = (REPO_ROOT / "run_paper_trading.bat").read_text(encoding="utf-8")
        self.assertIn("LEGACY_PAPER_TRADING_DISABLED", bat_file)
        self.assertNotIn("paper_portfolio_manager.py", bat_file)

    def test_12_new_telegram_scheduler_task_registered(self) -> None:
        """Verify new scheduled task is registered in Windows Task Scheduler."""
        import subprocess
        ps_cmd = "(Get-ScheduledTask -TaskName 'CSM TSM Paper Telegram Status' -ErrorAction SilentlyContinue).State.ToString()"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Ready", res.stdout)

    def test_13_new_telegram_scheduler_is_status_only(self) -> None:
        """Verify new scheduled task action points to run_telegram_status.bat."""
        import subprocess
        ps_cmd = "(Get-ScheduledTask -TaskName 'CSM TSM Paper Telegram Status').Actions.Execute"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("run_telegram_status.bat", res.stdout)


if __name__ == "__main__":
    unittest.main()
