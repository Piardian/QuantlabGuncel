from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import requests


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]

SOURCE_CLOSE_PANEL = REPO_ROOT / "output" / "csm_001_cv001" / "adjusted_close_panel.csv"
DATA_DIR = REPO_ROOT / "data" / "rsm_001"
MONTHLY_RETURNS_FILE = DATA_DIR / "monthly_returns.csv"
FACTOR_RETURNS_FILE = DATA_DIR / "fama_french_3_factor_monthly.csv"
DATA_REPORT_FILE = DATA_DIR / "data_preparation_report.json"

KEN_FRENCH_FF3_MONTHLY_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def build_monthly_returns() -> dict[str, object]:
    if not SOURCE_CLOSE_PANEL.exists():
        raise FileNotFoundError(f"Missing adjusted close panel: {SOURCE_CLOSE_PANEL}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    close = pd.read_csv(SOURCE_CLOSE_PANEL, index_col=0, parse_dates=True)
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = close.sort_index()
    close = close.apply(pd.to_numeric, errors="coerce")
    monthly_close = close.resample("ME").last()
    monthly_returns = monthly_close.pct_change()
    monthly_returns = monthly_returns.dropna(how="all")
    monthly_returns.to_csv(MONTHLY_RETURNS_FILE)

    return {
        "source": _repo_relative(SOURCE_CLOSE_PANEL),
        "output": _repo_relative(MONTHLY_RETURNS_FILE),
        "rows": int(monthly_returns.shape[0]),
        "columns": int(monthly_returns.shape[1]),
        "first_month": str(monthly_returns.index.min().date()),
        "last_month": str(monthly_returns.index.max().date()),
    }


def download_fama_french_3_factor_monthly(timeout_seconds: int = 30) -> dict[str, object]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(KEN_FRENCH_FF3_MONTHLY_URL, timeout=timeout_seconds)
    response.raise_for_status()

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    member_name = archive.namelist()[0]
    lines = archive.read(member_name).decode("utf-8", errors="replace").splitlines()

    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith(",Mkt-RF,SMB,HML,RF"):
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("Could not locate Fama-French monthly factor header.")

    data_lines: list[str] = [lines[header_idx]]
    for line in lines[header_idx + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        first = stripped.split(",", 1)[0]
        if not first.isdigit() or len(first) != 6:
            break
        data_lines.append(line)

    factors = pd.read_csv(io.StringIO("\n".join(data_lines)))
    factors = factors.rename(columns={"Unnamed: 0": "month", "Mkt-RF": "mkt_rf", "RF": "rf"})
    factors.columns = [str(column).strip().lower().replace("-", "_") for column in factors.columns]
    factors["month"] = pd.to_datetime(factors["month"].astype(str), format="%Y%m").dt.to_period("M").dt.to_timestamp("M")
    for column in ["mkt_rf", "smb", "hml", "rf"]:
        factors[column] = pd.to_numeric(factors[column], errors="coerce") / 100.0
    factors = factors[["month", "mkt_rf", "smb", "hml", "rf"]].dropna()
    factors = factors.set_index("month").sort_index()
    factors.to_csv(FACTOR_RETURNS_FILE)

    return {
        "source": KEN_FRENCH_FF3_MONTHLY_URL,
        "archive_member": member_name,
        "output": _repo_relative(FACTOR_RETURNS_FILE),
        "rows": int(factors.shape[0]),
        "first_month": str(factors.index.min().date()),
        "last_month": str(factors.index.max().date()),
    }


def prepare_data() -> dict[str, object]:
    report: dict[str, object] = {
        "construct_id": "RSM-001",
        "stage": "IM-001 data preparation",
        "monthly_returns": None,
        "fama_french_factors": None,
        "status": "UNKNOWN",
    }
    report["monthly_returns"] = build_monthly_returns()
    try:
        report["fama_french_factors"] = download_fama_french_3_factor_monthly()
    except Exception as exc:
        report["fama_french_factors"] = {
            "source": KEN_FRENCH_FF3_MONTHLY_URL,
            "output": _repo_relative(FACTOR_RETURNS_FILE),
            "status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    factor_status = report["fama_french_factors"]
    report["status"] = "COMPLETE" if isinstance(factor_status, dict) and factor_status.get("status") != "FAILED" else "PARTIAL_FACTOR_DOWNLOAD_FAILED"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = prepare_data()
    print(json.dumps(result, indent=2))

