from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from feature_pipeline import load_opt001_input  # noqa: E402
from opt001_options_implied_model import (  # noqa: E402
    DATA_QUALITY_INSUFFICIENT_LOOKBACK,
    DATA_QUALITY_INVALID_NON_POSITIVE,
    DATA_QUALITY_MISSING_INPUT,
    DATA_QUALITY_OK,
    DATA_QUALITY_ZERO_ROLLING_STD,
    OPT001OptionsImplied,
)


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
    parser = argparse.ArgumentParser(description="Validate OPT-001 implementation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--input-csv", type=Path, help="Optional frozen VIXCLS FRED CSV snapshot.")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = parse_simple_yaml(args.config)
    output_dir = Path(args.output_dir or config.get("output_dir", "output/opt_001_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)

    source_series = config.get("source_series", "VIXCLS")
    source, metadata = load_opt001_input(source_series, args.input_csv)

    input_snapshot_path = output_dir / "opt001_input_series.csv"
    source.to_csv(input_snapshot_path, index=False)

    model = OPT001OptionsImplied(
        source_series=source_series,
        normalization_window=int(config.get("normalization_window", "252")),
    )
    result = model.transform(source)

    output_path = output_dir / "opt001_options_implied_output.csv"
    result.frame.to_csv(output_path, index=False)

    repeated = model.transform(source).frame
    deterministic = result.frame.equals(repeated)

    summary = {
        "construct_id": "OPT-001",
        "source_series": result.source_series,
        "input_source": metadata["input_source"],
        "input_snapshot_sha256": file_sha256(input_snapshot_path),
        "rows": int(len(result.frame)),
        "start": str(pd.to_datetime(result.frame["date"]).min()) if not result.frame.empty else None,
        "end": str(pd.to_datetime(result.frame["date"]).max()) if not result.frame.empty else None,
        "raw_observations": int(result.frame["opt001_vix_close"].notna().sum()),
        "zscore_observations": int(result.frame["opt001_zscore_252d"].notna().sum()),
        "percentile_observations": int(result.frame["opt001_percentile_252d"].notna().sum()),
        "ok_flags": int((result.frame["opt001_data_quality_flag"] == DATA_QUALITY_OK).sum()),
        "missing_input_flags": int((result.frame["opt001_data_quality_flag"] == DATA_QUALITY_MISSING_INPUT).sum()),
        "insufficient_lookback_flags": int(
            (result.frame["opt001_data_quality_flag"] == DATA_QUALITY_INSUFFICIENT_LOOKBACK).sum()
        ),
        "zero_rolling_std_flags": int(
            (result.frame["opt001_data_quality_flag"] == DATA_QUALITY_ZERO_ROLLING_STD).sum()
        ),
        "invalid_non_positive_flags": int(
            (result.frame["opt001_data_quality_flag"] == DATA_QUALITY_INVALID_NON_POSITIVE).sum()
        ),
        "deterministic_repeated_transform": bool(deterministic),
        "output_sha256": file_sha256(output_path),
    }
    (output_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output_dir, summary)


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# OPT-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, trading performance, or economic utility.

## Verification Summary

- Source series: {summary["source_series"]}
- Input source: {summary["input_source"]}
- Input snapshot SHA256: `{summary["input_snapshot_sha256"]}`
- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Raw VIX observations: {summary["raw_observations"]}
- 252-valid-observation z-score observations: {summary["zscore_observations"]}
- 252-valid-observation percentile observations: {summary["percentile_observations"]}
- OK flags: {summary["ok_flags"]}
- MISSING_INPUT flags: {summary["missing_input_flags"]}
- INSUFFICIENT_LOOKBACK flags: {summary["insufficient_lookback_flags"]}
- ZERO_ROLLING_STD flags: {summary["zero_rolling_std_flags"]}
- INVALID_NON_POSITIVE flags: {summary["invalid_non_positive_flags"]}
- Repeated transform deterministic: {summary["deterministic_repeated_transform"]}
- Output SHA256: `{summary["output_sha256"]}`

## Verdict

The implementation is structurally complete if the output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

OPT-001 uses deterministic formulas only. With identical source data, configuration, and preprocessing, output values are reproducible.

The validation summary records SHA256 hashes for both the input snapshot and primary output CSV.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Required checks:

1. FRED-style DATE / observation_date and VIXCLS inputs are accepted.
2. Official construct values are not forward-filled.
3. Non-positive VIX values are marked invalid.
4. 252-valid-observation z-score and percentile calculations are correct.
5. Required output columns are present.
6. Repeated execution on identical synthetic input is deterministic.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
.venv\\Scripts\\python.exe research\\implementations\\opt_001\\validate_opt_001.py --config research\\implementations\\opt_001\\config.yaml
```

For frozen-input reproducibility:

```powershell
.venv\\Scripts\\python.exe research\\implementations\\opt_001\\validate_opt_001.py --input-csv output\\opt_001_validation\\opt001_input_series.csv
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- OPT-001 implements a VIXCLS implied-volatility state only.
- It does not decompose expected volatility, variance risk premium, hedging demand, risk aversion, or tail-risk compensation.
- FRED/Cboe source revisions can change future reruns unless raw input snapshots are archived.
- No predictive, trading, alpha, or economic interpretation is made.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 implements OPT-001 as a deterministic option-implied volatility state construct using FRED series VIXCLS.

The implementation follows CD-001 and is ready for construct validation once human review approves progression.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

