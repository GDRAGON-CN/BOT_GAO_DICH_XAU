@echo off
echo Starting XAUUSD Trading Bot Backend (FastAPI)...
cd /d "%~dp0..\backend"
call python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
