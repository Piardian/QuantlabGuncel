# Windows Startup and Scheduler Setup

This project now has an operational paper-trading launcher for the frozen
`leadership_expansion_v1` strategy. The strategy code, entry logic, exit logic,
risk model, and portfolio rules are not modified by this automation layer.

## One-Time Windows Setup

1. Configure BIOS/UEFI automatic power-on.
2. Configure Windows automatic login.
3. Open Task Scheduler.
4. Create a task named `Leadership Paper Trading`.
5. Use the trigger `Weekly`, select Monday through Friday, and set it to
   `23:30` local time. Weekend messages are intentionally disabled because
   this end-of-day workflow targets market days only.
6. Use the action:

```text
Program/script:
C:\Users\piard\Desktop\backterster\run_paper_trading.bat

Start in:
C:\Users\piard\Desktop\backterster
```

7. Enable `Run as soon as possible after a scheduled start is missed`.
8. Enable `Wake the computer to run this task`.
9. On `Settings`, enable task restart every 5 minutes with 3 attempts.
10. Enable `Start only if the following network connection is available` if your
    Windows installation exposes that option.

## Startup Checks

The launcher always runs `startup_checks.py` before the paper workflow. This
verifies:

- Python environment availability
- Required Python packages
- `data/`
- `daily_logs/`
- `signals/`
- `automation/`

If you want a separate Windows startup-only check, create a second Task Scheduler
task:

```text
Trigger:
At log on

Program/script:
C:\Users\piard\Desktop\backterster\.venv\Scripts\python.exe

Add arguments:
startup_checks.py

Start in:
C:\Users\piard\Desktop\backterster
```

## Configurable Execution Time

The default intended execution time is 23:30 local time on Monday through
Friday. Change it only in Windows Task Scheduler. No Python code changes are
required.

## Outputs

Every scheduled run writes:

- `daily_logs/paper_trading_YYYYMMDD_HHMMSS.log`
- `daily_logs/paper_trading_YYYYMMDD_HHMMSS.json`
- `signals/daily_signal_report.csv`
- `paper_portfolio.csv`

## Manual Test Command

Run this once from PowerShell before relying on the scheduled task:

```powershell
cd "C:\Users\piard\Desktop\backterster"
.\run_paper_trading.bat
```

Optional ticker override:

```powershell
set PAPER_TICKERS=AAPL,NVDA,TSLA,SPY
.\run_paper_trading.bat
```
