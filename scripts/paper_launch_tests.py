import unittest
from unittest.mock import patch
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from scripts.paper_controlled_launch import run_preflight_checks

class TestPaperLaunch(unittest.TestCase):
    @patch.dict("os.environ", {"APCA_API_BASE_URL": "https://paper-api.alpaca.markets"})
    def test_preflight_success(self):
        self.assertTrue(run_preflight_checks())

    @patch.dict("os.environ", {"APCA_API_BASE_URL": "https://api.alpaca.markets"})
    def test_preflight_failure_live_endpoint(self):
        self.assertFalse(run_preflight_checks())

if __name__ == "__main__":
    unittest.main()
