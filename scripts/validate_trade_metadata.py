"""Compare core backtest results before and after journal metadata changes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


CORE_COLUMNS = [
    "entry_time", "exit_time", "direction", "entry_price", "exit_price",
    "stop_loss", "take_profit", "position_size", "pnl_dollars", "pnl_percent",
    "R_multiple", "trade_duration_bars", "exit_reason",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    before = pd.read_csv(args.before)
    after = pd.read_csv(args.after)
    missing = [column for column in CORE_COLUMNS if column not in before or column not in after]
    if missing:
        raise ValueError(f"Missing core columns: {missing}")

    before_core = before[CORE_COLUMNS].reset_index(drop=True)
    after_core = after[CORE_COLUMNS].reset_index(drop=True)
    identical = before_core.equals(after_core)
    rows = {
        "before_trade_count": len(before_core),
        "after_trade_count": len(after_core),
        "before_net_pnl": float(pd.to_numeric(before["pnl_dollars"], errors="coerce").sum()),
        "after_net_pnl": float(pd.to_numeric(after["pnl_dollars"], errors="coerce").sum()),
        "before_profit_factor": _profit_factor(before),
        "after_profit_factor": _profit_factor(after),
        "before_avg_R": float(pd.to_numeric(before["R_multiple"], errors="coerce").mean()),
        "after_avg_R": float(pd.to_numeric(after["R_multiple"], errors="coerce").mean()),
        "core_trade_records_identical": identical,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([rows]).to_csv(args.report, index=False)
    print("IDENTICAL" if identical else "DIFFERENT")
    print(args.report)


def _profit_factor(frame: pd.DataFrame) -> float:
    pnl = pd.to_numeric(frame["pnl_dollars"], errors="coerce")
    gross_loss = abs(float(pnl[pnl < 0].sum()))
    gross_profit = float(pnl[pnl > 0].sum())
    return gross_profit / gross_loss if gross_loss else float("inf")


if __name__ == "__main__":
    main()
