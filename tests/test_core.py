from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class CoreTestCase(unittest.TestCase):
    def test_root_path_exists(self) -> None:
        self.assertTrue(ROOT.exists())
        self.assertTrue((ROOT / "scripts").exists())

if __name__ == "__main__":
    unittest.main()
