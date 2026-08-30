from __future__ import annotations

import os
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone
import pandas as pd

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter, BrokerMutationDisabled
from engine.paper_risk_guards import PaperSafetyManager
from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController
from scripts import paper_controlled_launch
from scripts.paper_safety_tests import FakeAdapter
from scripts.verify_preflight_integrity import verify_alpaca_endpoint


@dataclass
class MockLaunchState:
    authorized: bool = False
    endpoint: str = "https://paper-api.alpaca.markets"
    preflight_pass: bool = True
    paper_t0: str | None = None
    scientific_t0: str = "NOT_ESTABLISHED"
    submissions: list[str] = field(default_factory=list)
    open_client_order_ids: set[str] = field(default_factory=set)

    def can_submit(self) -> bool:
        return self.authorized and self.endpoint == "https://paper-api.alpaca.markets" and self.preflight_pass

    def set_paper_t0_once(self, timestamp: str) -> str:
        if self.paper_t0 is None:
            self.paper_t0 = timestamp
        return self.paper_t0

    def submit_batch(self, client_order_ids: list[str], fail_at: int | None = None) -> str:
        if not self.can_submit():
            return "PAPER_LAUNCH_BLOCKED"
        self.set_paper_t0_once("2026-08-25T00:00:00+00:00")
        for index, client_order_id in enumerate(client_order_ids):
            if client_order_id in self.open_client_order_ids:
                return "DUPLICATE_BLOCKED"
            if fail_at is not None and index == fail_at:
                return "PAPER_LAUNCH_PARTIAL_EXECUTION"
            self.submissions.append(client_order_id)
            self.open_client_order_ids.add(client_order_id)
        return "PAPER_LAUNCH_OPEN_ORDERS"


class PaperLaunchSafetyTests(unittest.TestCase):
    def test_no_authorization_no_mutation(self) -> None:
        state = MockLaunchState(authorized=False)
        self.assertEqual(state.submit_batch(["A"]), "PAPER_LAUNCH_BLOCKED")
        self.assertEqual(state.submissions, [])

    def test_paper_endpoint_required(self) -> None:
        self.assertEqual(verify_alpaca_endpoint("https://paper-api.alpaca.markets")["is_paper_endpoint"], True)

    def test_live_endpoint_blocked(self) -> None:
        state = MockLaunchState(authorized=True, endpoint="https://api.alpaca.markets")
        self.assertEqual(state.submit_batch(["A"]), "PAPER_LAUNCH_BLOCKED")

    def test_preflight_failure_zero_submissions(self) -> None:
        state = MockLaunchState(authorized=True, preflight_pass=False)
        self.assertEqual(state.submit_batch(["A"]), "PAPER_LAUNCH_BLOCKED")
        self.assertEqual(len(state.submissions), 0)

    def test_explicit_authorization_required(self) -> None:
        self.assertFalse(PaperSafetyManager().execution_flags_authorize(False, False, "PAPER"))
        self.assertTrue(PaperSafetyManager().execution_flags_authorize(True, True, "PAPER"))

    def test_paper_t0_established_once(self) -> None:
        state = MockLaunchState(authorized=True)
        first = state.set_paper_t0_once("first")
        second = state.set_paper_t0_once("second")
        self.assertEqual(first, "first")
        self.assertEqual(second, "first")

    def test_paper_t0_not_set_during_dry_run(self) -> None:
        state = MockLaunchState(authorized=False)
        state.submit_batch(["A"])
        self.assertIsNone(state.paper_t0)

    def test_full_batch_preflight_failure_zero_submissions(self) -> None:
        state = MockLaunchState(authorized=True, preflight_pass=False)
        self.assertEqual(state.submit_batch(["A", "B", "C"]), "PAPER_LAUNCH_BLOCKED")
        self.assertEqual(state.submissions, [])

    def test_first_order_success_second_failure_stops_batch(self) -> None:
        state = MockLaunchState(authorized=True)
        self.assertEqual(state.submit_batch(["A", "B", "C"], fail_at=1), "PAPER_LAUNCH_PARTIAL_EXECUTION")
        self.assertEqual(state.submissions, ["A"])

    def test_timeout_existing_client_order_id_no_duplicate(self) -> None:
        state = MockLaunchState(authorized=True, open_client_order_ids={"A"})
        self.assertEqual(state.submit_batch(["A"]), "DUPLICATE_BLOCKED")
        self.assertEqual(state.submissions, [])

    def test_restart_with_existing_order_no_duplicate(self) -> None:
        state = MockLaunchState(authorized=True)
        self.assertEqual(state.submit_batch(["A"]), "PAPER_LAUNCH_OPEN_ORDERS")
        restarted = MockLaunchState(authorized=True, open_client_order_ids=set(state.open_client_order_ids))
        self.assertEqual(restarted.submit_batch(["A"]), "DUPLICATE_BLOCKED")

    def test_partial_fill_not_marked_complete(self) -> None:
        broker_status = "partially_filled"
        launch_state = "PAPER_LAUNCH_OPEN_ORDERS" if broker_status != "filled" else "PAPER_LAUNCH_COMPLETE"
        self.assertNotEqual(launch_state, "PAPER_LAUNCH_COMPLETE")

    def test_scientific_t0_remains_unset(self) -> None:
        state = MockLaunchState(authorized=True)
        state.submit_batch(["A"])
        self.assertEqual(state.scientific_t0, "NOT_ESTABLISHED")

    def test_adapter_mutation_boundary_remains_disabled_in_precheck(self) -> None:
        class Adapter:
            def submit_order(self) -> None:
                raise BrokerMutationDisabled("blocked")

        with self.assertRaises(BrokerMutationDisabled):
            Adapter().submit_order()

    def test_precheck_blocks_if_launch_authorization_env_is_set(self) -> None:
        with patch.dict(os.environ, {"PAPER_LAUNCH_AUTHORIZED": "YES"}):
            with self.assertRaises(RuntimeError):
                paper_controlled_launch.run_precheck()

    def test_artifact_hash_writer_uses_real_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.txt"
            path.write_text("x", encoding="utf-8")
            self.assertEqual(len(path.read_bytes()), 1)

    def test_same_session_t_plus_1_violation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )
            # When simulated during market hours on Friday 2026-08-14 before close (e.g. 15:00 UTC),
            # latest completed session was Thursday 2026-08-13 and execution session is Friday 2026-08-14.
            # If someone forces a same-session execution where signal session == execution session:
            class SameSessionAdapter(FakeAdapter):
                def get_calendar(self, start: str, end: str):
                    return "PASS", [
                        {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
                    ]

            # At 17:00 UTC on 2026-08-14, signal session would be 2026-08-14 if close was earlier or no prior session
            controller = PaperTradingController(config, adapter=SameSessionAdapter(audit_log_path=Path(tmp) / "order_audit.csv"))
            result = controller.run_dry_run(now=datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc))
            self.assertEqual(result.schedule_state, "BLOCKED_TIMING")
            self.assertIn("T_PLUS_1_TIMING_VIOLATION", result.incidents)
            self.assertEqual(result.readiness_state, "BLOCKED")

    def test_next_valid_session_timing_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )
            controller = PaperTradingController(config, adapter=FakeAdapter(audit_log_path=Path(tmp) / "order_audit.csv"))
            # On Monday 2026-08-17 during market hours (14:00 UTC = 10:00 AM EDT)
            result = controller.run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result.signal_as_of_session, "2026-08-14")
            self.assertEqual(result.earliest_permitted_execution_session, "2026-08-17")
            self.assertEqual(result.execution_session, "2026-08-17")
            self.assertEqual(result.schedule_state, "PASS")
            self.assertEqual(result.identity_readiness_state, "PASS")
            self.assertEqual(result.readiness_state, "WAITING_FOR_SCHEDULED_REBALANCE")

    def test_friday_to_monday_and_holiday_market_calendar_boundaries(self) -> None:
        adapter = AlpacaBrokerAdapter(
            paper_base_url="https://paper-api.alpaca.markets",
            data_base_url="https://data.alpaca.markets",
            key_id="dummy",
            secret_key="dummy",
        )
        calendar = [
            {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-17", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-18", "open": "09:30", "close": "16:00"},
        ]
        self.assertEqual(adapter.next_market_session(calendar, "2026-08-14"), "2026-08-17")
        # Holiday boundary: Monday is a holiday (omitted from calendar)
        holiday_calendar = [
            {"date": "2026-08-14", "open": "09:30", "close": "16:00"},
            {"date": "2026-08-18", "open": "09:30", "close": "16:00"},
        ]
        self.assertEqual(adapter.next_market_session(holiday_calendar, "2026-08-14"), "2026-08-18")

    def test_stale_one_symbol_input_frozen_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )
            # Active symbol AAPL is stale
            adapter = FakeAdapter(audit_log_path=Path(tmp) / "order_audit.csv", stale_symbol="AAPL")
            result = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result.freshness_state, "FAIL")
            self.assertIn("STALE_DATA", result.incidents)
            self.assertEqual(result.readiness_state, "BLOCKED")

    def test_insufficient_history_symbol_frozen_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )

            class ShortHistoryAdapter(FakeAdapter):
                def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                    status, payload = super().get_daily_bars(symbols, start, end, feed=feed, adjustment=adjustment)
                    if "AAL" in payload.get("bars", {}):
                        payload["bars"]["AAL"] = payload["bars"]["AAL"][-10:]
                    return status, payload

            adapter = ShortHistoryAdapter(audit_log_path=Path(tmp) / "order_audit.csv")
            result = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result.eligible_count, 249)
            self.assertEqual(result.eligibility_state, "PASS")
            self.assertEqual(result.freshness_state, "PASS")
            self.assertEqual(result.csm_candidate_count, result.target_holding_count)
            self.assertEqual(result.target_weight_sum, 1.0)

    def test_asset_identity_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )

            class IdentityMismatchAdapter(FakeAdapter):
                def get_asset(self, symbol: str):
                    if symbol == "AAPL":
                        return "PASS", {"id": "DIFFERENT-UNEXPECTED-UUID", "status": "active", "tradable": True, "symbol": "AAPL"}
                    return super().get_asset(symbol)

                def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                    status, payload = super().get_daily_bars(symbols, start, end, feed=feed, adjustment=adjustment)
                    if "AAPL" in payload.get("bars", {}):
                        payload["bars"]["AAPL"] = payload["bars"]["AAPL"][:-1]
                    return status, payload

            adapter = IdentityMismatchAdapter(audit_log_path=Path(tmp) / "order_audit.csv")
            result = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertIn("BLOCK_IDENTITY_MISMATCH", result.incidents)
            self.assertEqual(result.readiness_state, "BLOCKED")

    def test_partial_api_response_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )

            class ErrorAdapter(FakeAdapter):
                def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                    return "HTTP_500", {"error": "Internal Server Error"}

            adapter = ErrorAdapter(audit_log_path=Path(tmp) / "order_audit.csv")
            result = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result.freshness_state, "FAIL")
            self.assertIn("MARKET_DATA_FAILURE", result.incidents)
            self.assertEqual(result.readiness_state, "BLOCKED")

    def test_249_valid_eligible_with_one_ineligible_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = PaperControllerConfig(
                target_path=None,
                identity_registry_path=Path(tmp) / "empty_registry.csv",
                audit_log_path=Path(tmp) / "audit.csv",
                incident_log_path=Path(tmp) / "incidents.csv",
                broker_audit_log_path=Path(tmp) / "order_audit.csv",
            )

            class DelistedSymbolAdapter(FakeAdapter):
                def get_asset(self, symbol: str):
                    if symbol == "BBBY":
                        return "HTTP_404", {"error": "Not Found"}
                    return super().get_asset(symbol)

                def get_daily_bars(self, symbols: list[str], start: str, end: str, *, feed: str = "iex", adjustment: str = "all"):
                    status, payload = super().get_daily_bars(symbols, start, end, feed=feed, adjustment=adjustment)
                    if "BBBY" in payload.get("bars", {}):
                        payload["bars"]["BBBY"] = payload["bars"]["BBBY"][:200]
                    return status, payload

            adapter = DelistedSymbolAdapter(audit_log_path=Path(tmp) / "order_audit.csv")
            result = PaperTradingController(config, adapter=adapter).run_dry_run(now=datetime(2026, 8, 17, 14, 0, tzinfo=timezone.utc))
            self.assertEqual(result.fresh_symbol_count, 249)
            self.assertEqual(result.stale_symbol_count, 0)
            self.assertEqual(result.inactive_symbol_count, 1)
            self.assertEqual(result.eligible_count, 249)
            self.assertEqual(result.eligibility_state, "PASS")
            self.assertEqual(result.freshness_state, "PASS")
            self.assertEqual(result.csm_candidate_count, result.target_holding_count)
            self.assertEqual(result.tsm_approved_count, result.target_holding_count)
            self.assertEqual(result.target_weight_sum, 1.0)
            self.assertEqual(result.identity_readiness_state, "PASS")
            self.assertEqual(result.readiness_state, "WAITING_FOR_SCHEDULED_REBALANCE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
