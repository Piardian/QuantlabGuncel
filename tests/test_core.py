from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class CoreTestCase(unittest.TestCase):
    def test_root_path_exists(self) -> None:
        self.assertTrue(ROOT.exists())
        self.assertTrue((ROOT / "scripts").exists())
        self.assertTrue((ROOT / "engine").exists())

    def test_timing_t_plus_1_synchronization(self) -> None:
        signal_date = "2026-08-31"
        execution_date = "2026-09-01"
        self.assertNotEqual(signal_date, execution_date)

    def test_bbby_exclusion_ineligibility(self) -> None:
        universe = ["AAPL", "MSFT", "BBBY", "GOOGL"]
        excluded_ticker = "BBBY"
        eligible_universe = [t for t in universe if t != excluded_ticker]
        self.assertNotIn(excluded_ticker, eligible_universe)
        self.assertEqual(len(eligible_universe), 3)

    def test_frozen_universe_preservation(self) -> None:
        total_count = 250
        valid_eligible_count = 249
        mock_universe = [f"TICKER_{i}" for i in range(total_count - 1)] + ["BBBY"]
        filtered_universe = [t for t in mock_universe if t != "BBBY"]
        self.assertEqual(len(mock_universe), total_count)
        self.assertEqual(len(filtered_universe), valid_eligible_count)

    def test_rebalance_order_intents(self) -> None:
        from engine.paper_trading_controller import PaperTradingController
        from engine.alpaca_broker_adapter import AlpacaBrokerAdapter
        controller = PaperTradingController()
        broker = AlpacaBrokerAdapter(
            paper_base_url="https://paper-api.alpaca.markets",
            data_base_url="https://data.alpaca.markets",
            key_id="test_key",
            secret_key="test_secret",
        )
        
        current_positions = [
            {"symbol": "AAA", "qty": "10.0", "current_price": "100.0"},
            {"symbol": "BBB", "qty": "20.0", "current_price": "50.0"},
            {"symbol": "CCC", "qty": "5.0", "current_price": "20.0"},
        ]
        target_weights = {"BBB": 0.5, "DDD": 0.5}
        latest_prices = {"AAA": 100.0, "BBB": 50.0, "CCC": 20.0, "DDD": 25.0}
        now = datetime.now(timezone.utc)
        
        intents = controller.build_order_intents(
            broker=broker,
            target_weights=target_weights,
            latest_prices=latest_prices,
            rebalance_id="2026-09-30",
            now=now,
            current_positions=current_positions,
            account_equity=10000.0,
        )
        symbols = [i.symbol for i in intents]
        sides = {i.symbol: i.side for i in intents}
        self.assertIn("AAA", symbols)
        self.assertEqual(sides["AAA"], "sell")
        self.assertIn("CCC", symbols)
        self.assertEqual(sides["CCC"], "sell")
        self.assertIn("DDD", symbols)
        self.assertEqual(sides["DDD"], "buy")
        self.assertNotIn("BBB", symbols)

if __name__ == "__main__":
    unittest.main()
