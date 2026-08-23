from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from tsm001_momentum_model import TSM001MomentumModel


def _hash_frame(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _synthetic_close_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=320)
    up = np.linspace(100, 200, len(dates))
    down = np.linspace(200, 100, len(dates))
    flat = np.full(len(dates), 100.0)
    mixed = 100 + np.sin(np.arange(len(dates)) / 10.0)
    invalid = np.full(len(dates), np.nan)
    return pd.DataFrame(
        {
            "UP": up,
            "DOWN": down,
            "FLAT": flat,
            "MIXED": mixed,
            "INVALID": invalid,
        },
        index=dates,
    )


def run_validation() -> dict[str, object]:
    model = TSM001MomentumModel()
    panel = _synthetic_close_panel()
    first = model.transform(panel).frame
    second = model.transform(panel).frame

    expected_columns = [
        "date",
        "ticker",
        "adjusted_close",
        "price_t_minus_21",
        "price_t_minus_252",
        "tsm_return_12_1",
        "tsm001_direction_score",
        "tsm001_state",
        "tsm001_positive_state",
        "tsm001_negative_state",
        "tsm001_valid_observation",
    ]
    if list(first.columns) != expected_columns:
        raise AssertionError("TSM-001 output schema mismatch.")
    if _hash_frame(first) != _hash_frame(second):
        raise AssertionError("TSM-001 execution is not deterministic.")

    valid = first[first["tsm001_valid_observation"]]
    if valid.empty:
        raise AssertionError("Synthetic validation produced no valid observations.")

    latest_date = valid["date"].max()
    latest = valid[valid["date"] == latest_date].set_index("ticker")
    if latest.loc["UP", "tsm001_direction_score"] != 1.0 or latest.loc["UP", "tsm001_state"] != "POSITIVE":
        raise AssertionError("Positive state assignment failed.")
    if latest.loc["DOWN", "tsm001_direction_score"] != -1.0 or latest.loc["DOWN", "tsm001_state"] != "NEGATIVE":
        raise AssertionError("Negative state assignment failed.")
    if latest.loc["FLAT", "tsm001_direction_score"] != 0.0 or latest.loc["FLAT", "tsm001_state"] != "NEUTRAL":
        raise AssertionError("Neutral state assignment failed.")
    if first[first["ticker"] == "INVALID"]["tsm001_valid_observation"].any():
        raise AssertionError("Invalid all-missing series should not produce valid observations.")

    rejected_anchor = False
    try:
        TSM001MomentumModel(formation_anchor_trading_days=251).transform(panel)
    except ValueError:
        rejected_anchor = True
    if not rejected_anchor:
        raise AssertionError("Frozen formation anchor guard failed.")

    rejected_vol = False
    try:
        TSM001MomentumModel(volatility_scaling="included").transform(panel)
    except ValueError:
        rejected_vol = True
    if not rejected_vol:
        raise AssertionError("Frozen volatility scaling guard failed.")

    return {
        "rows": int(len(first)),
        "valid_rows": int(first["tsm001_valid_observation"].sum()),
        "first_valid_date": str(valid["date"].min().date()),
        "last_valid_date": str(valid["date"].max().date()),
        "deterministic_hash": _hash_frame(first),
        "status": "PASSED",
    }


if __name__ == "__main__":
    report = run_validation()
    for key, value in report.items():
        print(f"{key}: {value}")
