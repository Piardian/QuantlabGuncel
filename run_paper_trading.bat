@echo off
setlocal

cd /d "%~dp0"

if not exist "daily_logs" mkdir "daily_logs"
if not exist "signals" mkdir "signals"
if not exist "automation" mkdir "automation"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set LOG_STAMP=%%i
set BAT_LOG=daily_logs\launcher_%LOG_STAMP%.log

echo [%DATE% %TIME%] Starting paper trading launcher > "%BAT_LOG%"

powershell -NoProfile -Command "$d=(Get-Date).DayOfWeek; if ($d -eq 'Saturday' -or $d -eq 'Sunday') { exit 2 } else { exit 0 }"
if %ERRORLEVEL% EQU 2 (
    echo [%DATE% %TIME%] Weekend detected. Paper trading run skipped. >> "%BAT_LOG%"
    exit /b 0
)

set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe

%PYTHON_EXE% --version >> "%BAT_LOG%" 2>&1
if errorlevel 1 (
    echo Python environment verification failed. >> "%BAT_LOG%"
    exit /b 1
)

%PYTHON_EXE% startup_checks.py >> "%BAT_LOG%" 2>&1
if errorlevel 1 (
    echo Startup checks failed. >> "%BAT_LOG%"
    exit /b 1
)

%PYTHON_EXE% paper_portfolio_manager.py >> "%BAT_LOG%" 2>&1
set RUN_EXIT=%ERRORLEVEL%

echo [%DATE% %TIME%] Paper trading launcher finished with code %RUN_EXIT% >> "%BAT_LOG%"
exit /b %RUN_EXIT%
