@echo off
echo Starting XAUUSD Trading Bot Backend and Frontend...

start "Trading Bot Backend" cmd /k "cd ..\..\backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
start "Trading Bot Dashboard" cmd /k "cd ..\..\frontend && npm run dev"

echo System started. Open http://localhost:5173 for Dashboard.
pause
