from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cor001_correlation_pipeline import COR001Config, compute_cor001, frame_sha256


def build_synthetic_close_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=420)
    data: dict[str, np.ndarray] = {}
    for idx in range(65):
        returns = np.array(
            [
                0.0004
                + 0.008 * np.sin(day / 13.0)
                + (0.0008 + idx * 0.00001) * np.cos((day + idx) / 7.0)
                + (idx % 5) * 0.00015 * np.sin(day / 3.0)
                for day in range(len(dates))
            ],
            dtype="float64",
        )
        series = (100.0 + idx) * np.exp(np.cumsum(returns))
        if idx >= 60:
            series = series.copy()
            series[:80] = np.nan
        data[f"T{idx:03d}"] = series

    return pd.DataFrame(data, index=dates)


def run_verification() -> dict[str, object]:
    config = COR001Config(
        universe_path="synthetic",
        start_date="2020-01-01",
        end_date="2021-12-31",
        minimum_eligible_count=50,
    )
    close_panel = build_synthetic_close_panel()
    first = compute_cor001(close_panel, config)
    second = compute_cor001(close_panel, config)

    hash_first = frame_sha256(first)
    hash_second = frame_sha256(second)

    first_valid = first[first["cor001_avg_pairwise_corr_60d"].notna()].iloc[0]
    last_row = first.iloc[-1]
    first_valid_index = first[first["cor001_avg_pairwise_corr_60d"].notna()].index[0]
    returns = np.log(close_panel / close_panel.shift(1))
    manual_window = returns.iloc[first_valid_index - config.correlation_window + 1 : first_valid_index + 1]
    manual_corr = manual_window.dropna(axis=1, how="any").corr()
    manual_values = manual_corr.to_numpy()[np.triu(np.ones(manual_corr.shape, dtype=bool), k=1)]
    manual_mean = float(np.nanmean(manual_values))

    expected_pair_count_first = int(60 * 59 / 2)
    expected_pair_count_last = int(65 * 64 / 2)

    checks = {
        "output_columns_match": list(first.columns)
        == [
            "date",
            "cor001_avg_pairwise_corr_60d",
            "cor001_zscore_252d",
            "cor001_percentile_252d",
            "cor001_eligible_security_count",
            "cor001_pair_count",
            "cor001_coverage_ratio",
        ],
        "deterministic_hash_match": hash_first == hash_second,
        "minimum_eligible_count_enforced": int(first_valid["cor001_eligible_security_count"]) >= 50,
        "first_valid_eligible_count_expected": int(first_valid["cor001_eligible_security_count"]) == 60,
        "first_valid_pair_count_expected": int(first_valid["cor001_pair_count"]) == expected_pair_count_first,
        "last_pair_count_expected": int(last_row["cor001_pair_count"]) == expected_pair_count_last,
        "manual_correlation_mean_match": abs(
            float(first_valid["cor001_avg_pairwise_corr_60d"]) - manual_mean
        )
        < 1e-12,
        "raw_correlation_in_valid_range": -1.0 <= float(first_valid["cor001_avg_pairwise_corr_60d"]) <= 1.0,
        "normalization_available_after_warmup": pd.notna(last_row["cor001_zscore_252d"])
        and pd.notna(last_row["cor001_percentile_252d"]),
    }

    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "rows": int(len(first)),
        "valid_observations": int(first["cor001_avg_pairwise_corr_60d"].notna().sum()),
        "sha256": hash_first,
    }


def main() -> None:
    result = run_verification()
    output = Path("research/implementation_verification/cor_001/verification_result.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
