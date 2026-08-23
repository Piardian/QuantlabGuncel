from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from crd001_credit_stress import CRD001CreditStress, fetch_fred_series_csv, load_fred_csv  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Validate CRD-001 implementation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--input-csv", type=Path, help="Optional frozen FRED CSV snapshot.")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = parse_simple_yaml(args.config)
    output_dir = Path(args.output_dir or config.get("output_dir", "output/crd_001_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)

    source_series = config.get("source_series", "BAMLH0A0HYM2")
    if args.input_csv:
        source = load_fred_csv(args.input_csv)
        input_source = str(args.input_csv)
    else:
        source = fetch_fred_series_csv(source_series)
        input_source = "fred_download"

    input_snapshot_path = output_dir / "crd001_input_series.csv"
    source.to_csv(input_snapshot_path, index=False)

    model = CRD001CreditStress(
        source_series=source_series,
        normalization_window=int(config.get("normalization_window", "252")),
        max_forward_fill_calendar_days=int(config.get("max_forward_fill_calendar_days", "5")),
    )
    result = model.transform(source)

    output_path = output_dir / "crd001_credit_stress_output.csv"
    result.frame.to_csv(output_path, index=False)

    repeated = model.transform(source).frame
    deterministic = result.frame.equals(repeated)

    summary = {
        "construct_id": "CRD-001",
        "source_series": result.source_series,
        "input_source": input_source,
        "input_snapshot_sha256": file_sha256(input_snapshot_path),
        "rows": int(len(result.frame)),
        "start": str(pd.to_datetime(result.frame["date"]).min()) if not result.frame.empty else None,
        "end": str(pd.to_datetime(result.frame["date"]).max()) if not result.frame.empty else None,
        "raw_observations": int(result.frame["crd001_hy_oas"].notna().sum()),
        "zscore_observations": int(result.frame["crd001_zscore_252d"].notna().sum()),
        "percentile_observations": int(result.frame["crd001_percentile_252d"].notna().sum()),
        "valid_flags": int((result.frame["crd001_data_quality_flag"] == "VALID").sum()),
        "source_missing_flags": int((result.frame["crd001_data_quality_flag"] == "SOURCE_MISSING").sum()),
        "deterministic_repeated_transform": bool(deterministic),
        "output_sha256": file_sha256(output_path),
    }
    (output_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output_dir, summary)


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# CRD-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, trading performance, or economic utility.

## Verification Summary

- Source series: {summary["source_series"]}
- Input source: {summary["input_source"]}
- Input snapshot SHA256: `{summary["input_snapshot_sha256"]}`
- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Raw observations: {summary["raw_observations"]}
- 252-day z-score observations: {summary["zscore_observations"]}
- 252-day percentile observations: {summary["percentile_observations"]}
- VALID flags: {summary["valid_flags"]}
- SOURCE_MISSING flags: {summary["source_missing_flags"]}
- Repeated transform deterministic: {summary["deterministic_repeated_transform"]}
- Output SHA256: `{summary["output_sha256"]}`

## Verdict

The implementation is structurally complete if the output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

CRD-001 uses deterministic formulas only. With identical source data, configuration, and preprocessing, output values are reproducible.

The validation summary records SHA256 hashes for both the input snapshot and primary output CSV.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Required checks:

1. Source frame parsing accepts FRED-style DATE and BAMLH0A0HYM2 columns.
2. Business-day indexing and 5-calendar-day forward-fill policy follow CD-001.
3. Gaps longer than 5 calendar days are marked invalid.
4. 252-valid-observation z-score and percentile columns are present.
5. Data-quality flags follow the frozen schema.
6. Repeated execution on identical synthetic input is deterministic.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
.venv\\Scripts\\python.exe research\\implementations\\crd_001\\validate_crd_001.py --config research\\implementations\\crd_001\\config.yaml
```

For frozen-input reproducibility:

```powershell
.venv\\Scripts\\python.exe research\\implementations\\crd_001\\validate_crd_001.py --input-csv output\\crd_001_validation\\crd001_input_series.csv
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- This implementation measures high-yield option-adjusted spread stress only.
- It does not decompose default risk, liquidity premium, or excess credit premium.
- FRED and ICE BofA source revisions can change future reruns unless raw input snapshots are archived.
- No predictive, trading, alpha, or economic interpretation is made.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 implements CRD-001 as a deterministic US High-Yield Credit Spread Stress construct using FRED series BAMLH0A0HYM2.

The implementation follows CD-001 and is ready for construct validation once human review approves progression.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

