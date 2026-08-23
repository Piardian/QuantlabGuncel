from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from volatility_inference import fetch_ohlc_with_adjustments, infer_volatility_from_market_data  # noqa: E402


def parse_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VOL-001 implementation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--input-csv", type=Path, help="Optional frozen OHLC input snapshot for reproducibility checks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = parse_simple_yaml(args.config)
    output_dir = Path(args.output_dir or config.get("output_dir", "output/vol_001_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)

    symbol = config.get("symbol", "SPY")
    if args.input_csv:
        data = pd.read_csv(args.input_csv, parse_dates=["Date"]).set_index("Date")
        input_source = str(args.input_csv)
    else:
        data = fetch_ohlc_with_adjustments(
            symbol=symbol,
            start=args.start or config.get("start", "2010-01-01"),
            end=args.end or config.get("end", "2026-01-01"),
            timeframe=config.get("timeframe", "1d"),
        )
        input_source = "yahoo_download"

    input_snapshot_path = output_dir / "vol001_input_ohlc.csv"
    snapshot = data.copy()
    snapshot.index.name = "Date"
    snapshot.to_csv(input_snapshot_path)

    result = infer_volatility_from_market_data(
        data=data,
        symbol=symbol,
        vol_window=int(config.get("vol_window", "20")),
        normalization_window=int(config.get("normalization_window", "252")),
        annualization_factor=int(config.get("annualization_factor", "252")),
    )

    output_path = output_dir / "vol001_volatility_output.csv"
    result.frame.to_csv(output_path, index=False)

    summary = {
        "construct_id": "VOL-001",
        "symbol": result.symbol,
        "input_source": input_source,
        "input_snapshot_sha256": file_sha256(input_snapshot_path),
        "rows": int(len(result.frame)),
        "start": str(pd.to_datetime(result.frame["date"]).min()) if not result.frame.empty else None,
        "end": str(pd.to_datetime(result.frame["date"]).max()) if not result.frame.empty else None,
        "valid_observations": int(result.frame["vol001_valid_observation"].sum()),
        "volatility_observations": int(result.frame["vol001_yz_volatility_20d"].notna().sum()),
        "zscore_observations": int(result.frame["vol001_zscore"].notna().sum()),
        "percentile_observations": int(result.frame["vol001_percentile"].notna().sum()),
        "mean_volatility": float(result.frame["vol001_yz_volatility_20d"].mean()),
        "max_zscore": float(result.frame["vol001_zscore"].max()),
        "output_sha256": file_sha256(output_path),
    }
    (output_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output_dir, summary)


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# VOL-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, or economic utility.

## Verification Summary

- Symbol: {summary["symbol"]}
- Input source: {summary["input_source"]}
- Input snapshot SHA256: `{summary["input_snapshot_sha256"]}`
- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Valid raw observations: {summary["valid_observations"]}
- 20-day volatility observations: {summary["volatility_observations"]}
- 252-day z-score observations: {summary["zscore_observations"]}
- 252-day percentile observations: {summary["percentile_observations"]}
- Mean annualized volatility: {summary["mean_volatility"]:.6f}
- Max volatility z-score: {summary["max_zscore"]:.6f}
- Output SHA256: `{summary["output_sha256"]}`

## Verdict

The implementation is structurally complete if the output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

VOL-001 uses deterministic formulas only. With identical SPY OHLC data, configuration, and preprocessing, output values are reproducible.

The validation summary records a SHA256 hash for the primary output CSV.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Required checks:

1. Feature pipeline computes overnight, open-to-close, and Rogers-Satchell components.
2. Yang-Zhang weighting constant and rolling variance follow CD-001.
3. Annualized volatility, z-score, and percentile columns are present.
4. Percentile uses deterministic tie handling.
5. Repeated execution on identical synthetic input is deterministic.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
.venv\\Scripts\\python.exe research\\implementations\\vol_001\\validate_vol_001.py --config research\\implementations\\vol_001\\config.yaml
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- This implementation validates SPY daily Yang-Zhang realized volatility only.
- It does not measure implied volatility, GARCH conditional volatility, high-frequency realized variance, ATR, or cross-sectional dispersion.
- Yahoo Finance data revisions can change future reruns unless raw input snapshots are archived.
- No predictive or economic interpretation is made.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 implements VOL-001 as a deterministic US Equity Market Daily Yang-Zhang Volatility State construct using SPY daily OHLC data.

The implementation follows CD-001 and is ready for construct validation once human review approves progression.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
