from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.paper_trading_controller import PAPER001R_DIR, PaperTradingController, result_to_dict


def main() -> int:
    PAPER001R_DIR.mkdir(parents=True, exist_ok=True)
    result = PaperTradingController().run_dry_run()
    payload = result_to_dict(result)
    path = PAPER001R_DIR / "paper001r_readiness_result.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"readiness_state": result.readiness_state, "submission_authorized": result.submission_authorized, "block_reason": result.block_reason}, sort_keys=True))
    return 0 if result.readiness_state == "READY_FOR_CONTROLLED_PAPER_LAUNCH" and not result.submission_authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
