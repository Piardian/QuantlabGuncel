from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


SIGNALS_DIR = Path("signals")
DAILY_SIGNAL_REPORT = SIGNALS_DIR / "daily_signal_report.csv"


@dataclass(slots=True)
class SignalRecord:
    date: str
    ticker: str
    signal_type: str
    entry_price: float
    stop_price: float
    risk_per_trade: float
    position_size: int
    strategy_name: str


def write_daily_signal_report(
    signals: list[SignalRecord],
    output_path: Path = DAILY_SIGNAL_REPORT,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [field_name for field_name in SignalRecord.__dataclass_fields__]
    dataframe = pd.DataFrame([asdict(signal) for signal in signals], columns=columns)
    dataframe.to_csv(output_path, index=False)
    return output_path
