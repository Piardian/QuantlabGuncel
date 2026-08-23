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
    result1 = PaperTradingController().run_dry_run()
    result2 = PaperTradingController().run_dry_run()
    comparable1 = result_to_dict(result1)
    comparable2 = result_to_dict(result2)
    for payload in (comparable1, comparable2):
        payload.pop("paper_session_id", None)
    reproducible = comparable1 == comparable2
    payload = result_to_dict(result1)
    payload["reproducibility_pass"] = reproducible
    path = PAPER001R_DIR / "paper001r_end_to_end_dry_run.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"readiness_state": result1.readiness_state, "submission_authorized": result1.submission_authorized, "reproducibility_pass": reproducible}, sort_keys=True))
    return 0 if result1.readiness_state == "READY_FOR_CONTROLLED_PAPER_LAUNCH" and not result1.submission_authorized and reproducible else 2


if __name__ == "__main__":
    raise SystemExit(main())
