from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
DATA_DIR = REPO_ROOT / "data" / "ism_001"
INDUSTRY_RETURNS_FILE = DATA_DIR / "ken_french_49_industry_value_weighted_monthly.csv"
DATA_REPORT_FILE = DATA_DIR / "data_preparation_report.json"

KEN_FRENCH_49_INDUSTRY_MONTHLY_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "49_Industry_Portfolios_CSV.zip"
)


def _repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _clean_industry_id(name: object) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(name).strip()).strip("_").upper()
    return cleaned or "UNKNOWN"


def _parse_monthly_value_weighted_section(lines: list[str]) -> tuple[pd.DataFrame, str]:
    header_idx = None
    for idx, line in enumerate(lines):
        fields = [field.strip() for field in line.split(",")]
        if fields[0] == "" and len(fields) >= 30 and any(field.lower() == "agric" for field in fields):
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("Could not locate Ken French 49 Industry monthly value-weighted header.")

    data_lines = [lines[header_idx]]
    for line in lines[header_idx + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        first = stripped.split(",", 1)[0].strip()
        if not first.isdigit() or len(first) != 6:
            break
        data_lines.append(line)

    raw = pd.read_csv(io.StringIO("\n".join(data_lines)))
    raw = raw.rename(columns={raw.columns[0]: "month"})
    industry_columns = [column for column in raw.columns if column != "month"]
    id_lookup = {column: _clean_industry_id(column) for column in industry_columns}
    if len(set(id_lookup.values())) != len(id_lookup):
        raise ValueError("Industry identifier collision while parsing Ken French industry columns.")

    raw["month"] = pd.to_datetime(raw["month"].astype(str), format="%Y%m").dt.to_period("M").dt.to_timestamp("M")
    raw = raw.rename(columns=id_lookup)
    for column in id_lookup.values():
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
        raw[column] = raw[column].mask(raw[column].le(-99.0))
        raw[column] = raw[column] / 100.0

    frame = raw.set_index("month").sort_index()
    return frame[id_lookup.values()], archive_member_hint(lines)


def archive_member_hint(lines: list[str]) -> str:
    for line in lines[:20]:
        if "49 Industry Portfolios" in line:
            return line.strip()
    return "Ken French 49 Industry Portfolios CSV"


def download_ken_french_49_industry_monthly(timeout_seconds: int = 30) -> dict[str, object]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(KEN_FRENCH_49_INDUSTRY_MONTHLY_URL, timeout=timeout_seconds)
    response.raise_for_status()

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    member_name = archive.namelist()[0]
    lines = archive.read(member_name).decode("utf-8", errors="replace").splitlines()
    industry_returns, section_hint = _parse_monthly_value_weighted_section(lines)
    industry_returns.to_csv(INDUSTRY_RETURNS_FILE)

    return {
        "source": KEN_FRENCH_49_INDUSTRY_MONTHLY_URL,
        "archive_member": member_name,
        "section_hint": section_hint,
        "output": _repo_relative(INDUSTRY_RETURNS_FILE),
        "rows": int(industry_returns.shape[0]),
        "columns": int(industry_returns.shape[1]),
        "first_month": str(industry_returns.index.min().date()),
        "last_month": str(industry_returns.index.max().date()),
        "status": "COMPLETE",
    }


def prepare_data() -> dict[str, object]:
    report = {
        "construct_id": "ISM-001",
        "stage": "IM-001 data preparation",
        "ken_french_49_industry_returns": None,
        "status": "UNKNOWN",
    }
    try:
        report["ken_french_49_industry_returns"] = download_ken_french_49_industry_monthly()
        report["status"] = "COMPLETE"
    except Exception as exc:
        report["ken_french_49_industry_returns"] = {
            "source": KEN_FRENCH_49_INDUSTRY_MONTHLY_URL,
            "output": _repo_relative(INDUSTRY_RETURNS_FILE),
            "status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        report["status"] = "FAILED"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(prepare_data(), indent=2))
