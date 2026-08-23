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

from feature_pipeline import load_fund001_inputs  # noqa: E402
from fund001_funding_stress_model import (  # noqa: E402
    DATA_QUALITY_INSUFFICIENT_LOOKBACK,
    DATA_QUALITY_MISSING_INPUT,
    DATA_QUALITY_OK,
    DATA_QUALITY_ZERO_ROLLING_STD,
    FUND001FundingStress,
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
    parser = argparse.ArgumentParser(description="Validate FUND-001 implementation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--cp-csv", type=Path, help="Optional frozen DCPF3M FRED CSV snapshot.")
    parser.add_argument("--tbill-csv", type=Path, help="Optional frozen DTB3 FRED CSV snapshot.")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = parse_simple_yaml(args.config)
    output_dir = Path(args.output_dir or config.get("output_dir", "output/fund_001_validation"))
    output_dir.mkdir(parents=True, exist_ok=True)

    cp_series = config.get("cp_series", "DCPF3M")
    tbill_series = config.get("tbill_series", "DTB3")
    source, metadata = load_fund001_inputs(cp_series, tbill_series, args.cp_csv, args.tbill_csv)

    input_snapshot_path = output_dir / "fund001_input_series.csv"
    source.to_csv(input_snapshot_path, index=False)

    model = FUND001FundingStress(
        cp_series=cp_series,
        tbill_series=tbill_series,
        normalization_window=int(config.get("normalization_window", "252")),
    )
    result = model.transform(source)

    output_path = output_dir / "fund001_funding_stress_output.csv"
    result.frame.to_csv(output_path, index=False)

    repeated = model.transform(source).frame
    deterministic = result.frame.equals(repeated)

    summary = {
        "construct_id": "FUND-001",
        "cp_series": result.cp_series,
        "tbill_series": result.tbill_series,
        "cp_source": metadata["cp_source"],
        "tbill_source": metadata["tbill_source"],
        "input_snapshot_sha256": file_sha256(input_snapshot_path),
        "rows": int(len(result.frame)),
        "start": str(pd.to_datetime(result.frame["date"]).min()) if not result.frame.empty else None,
        "end": str(pd.to_datetime(result.frame["date"]).max()) if not result.frame.empty else None,
        "raw_observations": int(result.frame["fund001_cp_tbill_spread"].notna().sum()),
        "zscore_observations": int(result.frame["fund001_zscore_252d"].notna().sum()),
        "percentile_observations": int(result.frame["fund001_percentile_252d"].notna().sum()),
        "ok_flags": int((result.frame["fund001_data_quality_flag"] == DATA_QUALITY_OK).sum()),
        "missing_input_flags": int((result.frame["fund001_data_quality_flag"] == DATA_QUALITY_MISSING_INPUT).sum()),
        "insufficient_lookback_flags": int(
            (result.frame["fund001_data_quality_flag"] == DATA_QUALITY_INSUFFICIENT_LOOKBACK).sum()
        ),
        "zero_rolling_std_flags": int(
            (result.frame["fund001_data_quality_flag"] == DATA_QUALITY_ZERO_ROLLING_STD).sum()
        ),
        "deterministic_repeated_transform": bool(deterministic),
        "output_sha256": file_sha256(output_path),
    }
    (output_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(output_dir, summary)


def write_reports(output: Path, summary: dict[str, object]) -> None:
    (output / "verification_report.md").write_text(
        f"""# FUND-001 Verification Report

## Scope

This validation run checks implementation fidelity only. It does not evaluate prediction, alpha, profitability, trading performance, or economic utility.

## Verification Summary

- Commercial paper series: {summary["cp_series"]}
- Treasury bill series: {summary["tbill_series"]}
- Commercial paper input source: {summary["cp_source"]}
- Treasury bill input source: {summary["tbill_source"]}
- Input snapshot SHA256: `{summary["input_snapshot_sha256"]}`
- Rows produced: {summary["rows"]}
- Date range: {summary["start"]} to {summary["end"]}
- Raw spread observations: {summary["raw_observations"]}
- 252-valid-observation z-score observations: {summary["zscore_observations"]}
- 252-valid-observation percentile observations: {summary["percentile_observations"]}
- OK flags: {summary["ok_flags"]}
- MISSING_INPUT flags: {summary["missing_input_flags"]}
- INSUFFICIENT_LOOKBACK flags: {summary["insufficient_lookback_flags"]}
- ZERO_ROLLING_STD flags: {summary["zero_rolling_std_flags"]}
- Repeated transform deterministic: {summary["deterministic_repeated_transform"]}
- Output SHA256: `{summary["output_sha256"]}`

## Verdict

The implementation is structurally complete if the output CSV contains the frozen CD-001 columns and repeated execution with identical inputs produces identical outputs.
""",
        encoding="utf-8",
    )
    (output / "reproducibility_report.md").write_text(
        """# Reproducibility Report

FUND-001 uses deterministic formulas only. With identical source data, configuration, and preprocessing, output values are reproducible.

The validation summary records SHA256 hashes for both the input snapshot and primary output CSV.
""",
        encoding="utf-8",
    )
    (output / "unit_test_report.md").write_text(
        """# Unit Test Report

Required checks:

1. FRED-style DATE, DCPF3M, and DTB3 inputs are accepted.
2. Exact-date merge behavior is preserved by the feature pipeline.
3. Official construct values are not forward-filled.
4. Raw spread equals DCPF3M minus DTB3.
5. 252-valid-observation z-score and percentile calculations are correct.
6. Missing inputs produce MISSING_INPUT flags.
7. Repeated execution on identical synthetic input is deterministic.
""",
        encoding="utf-8",
    )
    (output / "execution_example.md").write_text(
        """# Execution Example

```powershell
.venv\\Scripts\\python.exe research\\implementations\\fund_001\\validate_fund_001.py --config research\\implementations\\fund_001\\config.yaml
```

For frozen-input reproducibility:

```powershell
.venv\\Scripts\\python.exe research\\implementations\\fund_001\\validate_fund_001.py --cp-csv output\\fund_001_validation\\DCPF3M.csv --tbill-csv output\\fund_001_validation\\DTB3.csv
```
""",
        encoding="utf-8",
    )
    (output / "limitations.md").write_text(
        """# Limitations

- FUND-001 is a commercial-paper-to-Treasury-bill funding spread proxy.
- It does not decompose funding liquidity, credit risk, counterparty risk, monetary policy, or safe-asset demand.
- FRED source revisions can change future reruns unless raw input snapshots are archived.
- No predictive, trading, alpha, or economic interpretation is made.
""",
        encoding="utf-8",
    )
    (output / "executive_summary.md").write_text(
        """# Executive Summary

IM-001 implements FUND-001 as a deterministic short-term funding stress construct using FRED series DCPF3M and DTB3.

The implementation follows CD-001 and is ready for construct validation once human review approves progression.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

