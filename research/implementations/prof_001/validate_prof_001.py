from __future__ import annotations

import json
from pathlib import Path

from prof001_accounting_pipeline import PROF001AccountingPipeline


REPO_ROOT = Path(__file__).resolve().parents[3]
INPUT_FILE = REPO_ROOT / "data" / "prof_001" / "accounting_statements.csv"
OUTPUT_DIR = REPO_ROOT / "output" / "prof_001_validation"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = PROF001AccountingPipeline()
    status = "IMPLEMENTATION_INCOMPLETE"
    error = None
    rows = 0
    valid_rows = 0

    try:
        accounting = pipeline.load_accounting(INPUT_FILE)
        result = pipeline.build_features(accounting)
        rows = int(len(result))
        valid_rows = int(result["prof001_valid_observation"].sum())
        result.to_csv(OUTPUT_DIR / "prof001_gross_profitability_state.csv", index=False)
        status = "PASSED" if valid_rows > 0 else "IMPLEMENTATION_INCOMPLETE"
    except FileNotFoundError as exc:
        error = str(exc)
    except ValueError as exc:
        error = str(exc)

    summary = {
        "construct_id": "PROF-001",
        "stage": "IM-001",
        "status": status,
        "required_input_file": str(INPUT_FILE),
        "rows": rows,
        "valid_rows": valid_rows,
        "error": error,
    }
    (OUTPUT_DIR / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
