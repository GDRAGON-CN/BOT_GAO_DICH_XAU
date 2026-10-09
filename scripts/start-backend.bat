@echo off
title Gold Trading Bot - FastAPI Backend
echo =======================================================
echo Starting Gold Trading Bot - Backend Service
echo Environment: DEMO MODE (Local Windows)
echo =======================================================

cd /d "%~dp0\.."

REM Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Starting FastAPI with Uvicorn on http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
