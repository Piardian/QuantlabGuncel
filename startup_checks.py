from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
import sys


REQUIRED_DIRECTORIES = [
    Path("data"),
    Path("daily_logs"),
    Path("signals"),
    Path("automation"),
]
REQUIRED_FILES = [
    Path("config") / "telegram_config.json",
]
REQUIRED_PACKAGES = ["backtrader", "pandas", "yfinance"]


@dataclass(slots=True)
class CheckResult:
    name: str
    success: bool
    message: str


def run_startup_checks(base_dir: Path | None = None) -> list[CheckResult]:
    root = (base_dir or Path.cwd()).resolve()
    results: list[CheckResult] = []

    results.append(
        CheckResult(
            name="python_version",
            success=sys.version_info >= (3, 10),
            message=f"Python {sys.version.split()[0]} at {sys.executable}",
        )
    )

    for package_name in REQUIRED_PACKAGES:
        found = find_spec(package_name) is not None
        results.append(
            CheckResult(
                name=f"package:{package_name}",
                success=found,
                message="available" if found else "missing",
            )
        )

    for directory in REQUIRED_DIRECTORIES:
        path = root / directory
        try:
            path.mkdir(parents=True, exist_ok=True)
            success = path.exists() and path.is_dir()
            message = str(path)
        except OSError as exc:
            success = False
            message = str(exc)
        results.append(CheckResult(name=f"directory:{directory.as_posix()}", success=success, message=message))

    for required_file in REQUIRED_FILES:
        path = root / required_file
        results.append(
            CheckResult(
                name=f"file:{required_file.as_posix()}",
                success=path.exists() and path.is_file(),
                message=str(path),
            )
        )

    return results


def assert_startup_checks(base_dir: Path | None = None) -> list[CheckResult]:
    results = run_startup_checks(base_dir)
    failures = [result for result in results if not result.success]
    if failures:
        formatted = "\n".join(f"- {failure.name}: {failure.message}" for failure in failures)
        raise RuntimeError(f"Startup checks failed:\n{formatted}")
    return results


def main() -> int:
    results = run_startup_checks()
    for result in results:
        status = "OK" if result.success else "FAIL"
        print(f"{status} | {result.name} | {result.message}")
    return 0 if all(result.success for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
