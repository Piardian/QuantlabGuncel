@echo off
setlocal

:: LEGACY PAPER TRADING LAUNCHER - RETIRED & DISABLED
:: The legacy daily leadership_expansion_v1 simulation has been retired.
:: The active system is the frozen monthly CSM-001 x TSM-001 strategy.
:: Status reporting is handled by scripts\paper_telegram_status.py via the "CSM TSM Paper Telegram Status" task.

echo [%DATE% %TIME%] LEGACY_PAPER_TRADING_DISABLED: leadership_expansion_v1 runner is retired. Execution skipped.
exit /b 0
