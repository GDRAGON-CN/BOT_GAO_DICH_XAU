@echo off
echo Starting XAUUSD Trading Bot Backend (Dev Mode)...
cd ..
call uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
