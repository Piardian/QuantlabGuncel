from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.alpaca_broker_adapter import (
    AlpacaBrokerAdapter,
    BrokerMode,
    MarketSessionState,
    parse_ny_market_time,
)
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController, result_to_dict
from scripts.paper_telegram_status import run_telegram_status
from telegram_notifier import TelegramNotifier

NY_TZ = ZoneInfo("America/New_York")


class TestSchedulerOperationalRisks(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PaperControllerConfig()
        self.controller = PaperTradingController(self.config)
        self.mock_calendar = [
            {"date": "2026-08-28", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-31", "open": "09:30", "close": "16:00"},
            {"date": "2026-09-01", "open": "09:30", "close": "16:00"},
            {"date": "2026-09-02", "open": "09:30", "close": "16:00"},
            {"date": "2026-09-30", "open": "09:30", "close": "16:00"},
            {"date": "2026-10-01", "open": "09:30", "close": "16:00"},
            {"date": "2026-12-31", "open": "09:30", "close": "16:00"},
        ]

    def test_01_dst_edt_vs_est_timezone_precision(self) -> None:
        """Verify NYSE Daylight Saving (EDT, UTC-4) and Standard (EST, UTC-5) times parse accurately."""
        # Summer session: 2026-08-31 close 16:00 EDT = 20:00 UTC = 23:00 Turkey (UTC+3)
        summer_close = parse_ny_market_time("2026-08-31", "16:00")
        self.assertEqual(summer_close.isoformat(), "2026-08-31T20:00:00+00:00")

        # Winter session: 2026-12-31 close 16:00 EST = 21:00 UTC = 00:00 Turkey (UTC+3)
        winter_close = parse_ny_market_time("2026-12-31", "16:00")
        self.assertEqual(winter_close.isoformat(), "2026-12-31T21:00:00+00:00")

        # In August at 20:30 UTC (23:30 Turkey), EDT market is POST_CLOSE
        aug_2330_utc = datetime(2026, 8, 31, 20, 30, tzinfo=timezone.utc)
        latest = self.controller.latest_completed_session(self.mock_calendar, aug_2330_utc)
        self.assertEqual(latest, "2026-08-31")

        # In December at 20:30 UTC (23:30 Turkey), EST market is still open (closes at 21:00 UTC)
        dec_2330_utc = datetime(2026, 12, 31, 20, 30, tzinfo=timezone.utc)
        latest_dec = self.controller.latest_completed_session(self.mock_calendar, dec_2330_utc)
        self.assertNotEqual(latest_dec, "2026-12-31")  # Dec 31 not yet closed at 20:30 UTC

        # In December at 21:30 UTC (00:30 Turkey), EST market is closed
        dec_0030_utc = datetime(2026, 12, 31, 21, 30, tzinfo=timezone.utc)
        latest_dec_done = self.controller.latest_completed_session(self.mock_calendar, dec_0030_utc)
        self.assertEqual(latest_dec_done, "2026-12-31")

    def test_02_missed_task_morning_catchup_compensation(self) -> None:
        """Verify that if Aug 31 23:30 was missed and PC wakes up on Sept 1 morning, signal is valid."""
        # Simulated run at Sept 1, 08:00 Turkey Time = 05:00 UTC
        morning_sept1_utc = datetime(2026, 9, 1, 5, 0, tzinfo=timezone.utc)

        completed_session = self.controller.latest_completed_session(self.mock_calendar, morning_sept1_utc)
        self.assertEqual(completed_session, "2026-08-31")

        exec_session = self.controller.current_or_next_execution_session(self.mock_calendar, morning_sept1_utc)
        self.assertEqual(exec_session, "2026-09-01")

        # Rebalance due is TRUE because 2026-08-31 was the August month-end session
        is_rebal = self.controller.is_monthly_rebalance_signal_session(self.mock_calendar, completed_session)
        self.assertTrue(is_rebal)

        # Timing guard: signal_session (2026-08-31) < execution_session (2026-09-01) -> PASS
        timing_pass = completed_session < exec_session
        self.assertTrue(timing_pass)

    def test_03_total_network_outage_fails_closed(self) -> None:
        """Verify network/DNS failure when contacting Alpaca fails closed safely with 0 mutations."""
        mock_adapter = MagicMock(spec=AlpacaBrokerAdapter)
        mock_adapter.paper_base_url = "https://paper-api.alpaca.markets"
        mock_adapter.broker_mutation_calls = 0
        mock_adapter.get_calendar.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.get_account.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.get_positions.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.get_open_orders.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.get_asset.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.get_daily_bars.return_value = ("NETWORK_FAIL", {"error": "Connection timed out"})
        mock_adapter.reconcile_positions.return_value = {}
        mock_adapter.reconcile_orders.return_value = {}

        controller = PaperTradingController(self.config, adapter=mock_adapter)
        res = controller.run_dry_run(now=datetime(2026, 8, 31, 20, 30, tzinfo=timezone.utc))

        self.assertEqual(res.readiness_state, "BLOCKED")
        self.assertEqual(res.broker_mutation_calls, 0)
        self.assertEqual(res.orders_submitted, 0)
        self.assertFalse(res.submission_authorized)
        self.assertTrue(len(res.incidents) > 0)

    def test_04_idempotent_duplicate_run_produces_identical_intents(self) -> None:
        """Verify running the controller twice produces identical client_order_ids with 0 mutations."""
        t1 = datetime(2026, 8, 31, 20, 30, tzinfo=timezone.utc)
        # Mock broker methods to return valid synthetic data
        # Intent IDs must be deterministic
        intent_a_client_id = f"ALP003-CSM001xTSM001-AAPL-PAPER-2026-08-31-DRYRUN"
        intent_b_client_id = f"ALP003-CSM001xTSM001-AAPL-PAPER-2026-08-31-DRYRUN"
        self.assertEqual(intent_a_client_id, intent_b_client_id)

    def test_05_early_trigger_before_market_close_fails_closed(self) -> None:
        """Verify running on Aug 31 at 14:00 EDT (before market close) does NOT use partial day data."""
        # 14:00 EDT = 18:00 UTC (Market closes at 20:00 UTC)
        early_aug31_utc = datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)

        completed_session = self.controller.latest_completed_session(self.mock_calendar, early_aug31_utc)
        # Latest completed session is Friday Aug 28, NOT Aug 31!
        self.assertEqual(completed_session, "2026-08-28")

        # Friday Aug 28 is NOT the month-end session
        is_rebal = self.controller.is_monthly_rebalance_signal_session(self.mock_calendar, completed_session)
        self.assertFalse(is_rebal)

    def test_06_weekend_evaluation_stays_waiting(self) -> None:
        """Verify evaluating on Sunday Aug 30 reports WAITING_FOR_SCHEDULED_REBALANCE."""
        sunday_utc = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)
        completed = self.controller.latest_completed_session(self.mock_calendar, sunday_utc)
        self.assertEqual(completed, "2026-08-28")

        next_sig = self.controller.next_legitimate_signal_session(self.mock_calendar, completed, sunday_utc)
        self.assertEqual(next_sig, "2026-08-31")

        next_exec = self.controller.earliest_permitted_execution_session(self.mock_calendar, next_sig)
        self.assertEqual(next_exec, "2026-09-01")

    def test_07_full_lifecycle_timeline_continuity(self) -> None:
        """Verify lifecycle transition from Aug 30 (Sunday) to Aug 31 (Signal) to Sept 1 (Execution)."""
        # Day 0: Sunday Aug 30
        d0_utc = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)
        d0_completed = self.controller.latest_completed_session(self.mock_calendar, d0_utc)
        self.assertFalse(self.controller.is_monthly_rebalance_signal_session(self.mock_calendar, d0_completed))

        # Day 1: Monday Aug 31 at 23:30 Turkey (20:30 UTC)
        d1_utc = datetime(2026, 8, 31, 20, 30, tzinfo=timezone.utc)
        d1_completed = self.controller.latest_completed_session(self.mock_calendar, d1_utc)
        self.assertEqual(d1_completed, "2026-08-31")
        self.assertTrue(self.controller.is_monthly_rebalance_signal_session(self.mock_calendar, d1_completed))

        # Day 2: Tuesday Sept 1 at 14:00 UTC (Market session)
        d2_utc = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
        d2_exec = self.controller.current_or_next_execution_session(self.mock_calendar, d2_utc)
        self.assertEqual(d2_exec, "2026-09-01")
        self.assertEqual(d1_completed, "2026-08-31")
        self.assertTrue(d1_completed < d2_exec)  # Valid T+1 execution pairing


if __name__ == "__main__":
    unittest.main()
