@echo off
setlocal

echo 🚀 AlgoSignal AI: FastAPI Server Starting...

REM Load .env file if it exists
if exist .env (
    echo [INFO] Loading environment from .env...
    for /F "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" (
            set "%%A=%%B"
        )
    )
)

echo.
venv\Scripts\python.exe server.py
pause
