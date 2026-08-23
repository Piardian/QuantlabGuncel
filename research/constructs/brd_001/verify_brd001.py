from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from brd001_breadth_pipeline import BRD001Config, compute_brd001, frame_sha256


def build_synthetic_close_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=520)
    data: dict[str, list[float]] = {}

    for idx in range(60):
        ticker = f"T{idx:03d}"
        if idx < 30:
            data[ticker] = [100.0 + day * 0.20 + idx * 0.01 for day in range(len(dates))]
        elif idx < 45:
            data[ticker] = [
                180.0 - day * 0.08 + idx * 0.01 if day < 260 else 159.2 + (day - 260) * 0.30 + idx * 0.01
                for day in range(len(dates))
            ]
        else:
            data[ticker] = [200.0 - day * 0.10 + idx * 0.01 for day in range(len(dates))]

    return pd.DataFrame(data, index=dates)


def run_verification() -> dict[str, object]:
    config = BRD001Config(
        universe_path="synthetic",
        start_date="2020-01-01",
        end_date="2021-12-31",
        minimum_eligible_count=50,
    )
    close_panel = build_synthetic_close_panel()
    first = compute_brd001(close_panel, config)
    second = compute_brd001(close_panel, config)

    hash_first = frame_sha256(first)
    hash_second = frame_sha256(second)

    first_valid = first[first["brd001_valid_observation"]].iloc[0]
    last_valid = first[first["brd001_valid_observation"]].iloc[-1]

    checks = {
        "output_columns_match": list(first.columns)
        == [
            "date",
            "brd001_pct_above_sma200",
            "brd001_zscore",
            "brd001_percentile",
            "brd001_count_above_sma200",
            "brd001_count_not_above_sma200",
            "brd001_eligible_count",
            "brd001_total_universe_count",
            "brd001_coverage_ratio",
            "brd001_valid_observation",
        ],
        "deterministic_hash_match": hash_first == hash_second,
        "minimum_eligible_count_enforced": int(first_valid["brd001_eligible_count"]) == 60,
        "synthetic_count_above_expected": int(first_valid["brd001_count_above_sma200"]) == 30,
        "synthetic_pct_expected": abs(float(first_valid["brd001_pct_above_sma200"]) - 0.5) < 1e-12,
        "normalization_available_after_warmup": pd.notna(last_valid["brd001_zscore"])
        and pd.notna(last_valid["brd001_percentile"]),
    }

    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "rows": int(len(first)),
        "valid_observations": int(first["brd001_valid_observation"].sum()),
        "sha256": hash_first,
    }


def main() -> None:
    result = run_verification()
    output = Path("research/implementation_verification/brd_001/verification_result.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
