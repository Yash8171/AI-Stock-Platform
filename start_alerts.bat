@echo off
setlocal

echo ============================================================
echo   AlgoSignal AI -- Background Alert Engine
echo ============================================================
echo.

REM Load .env file if it exists
if exist .env (
    echo [INFO] Loading environment from .env...
    for /F "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" (
            set "%%A=%%B"
        )
    )
)

REM Alert job settings
set RUN_CONTINUOUS=true
set BYPASS_MARKET_CHECK=false
set ALERT_INTERVAL_SECONDS=900

echo [INFO] Alert interval : every 15 minutes (900s)
echo [INFO] Trading hours  : Mon-Fri 9:30 AM - 4:00 PM US/Eastern
echo [INFO] Sender email   : %SENDER_EMAIL%
echo [INFO] Press Ctrl+C to stop.
echo.

venv\Scripts\python.exe -u alert_job.py

pause
