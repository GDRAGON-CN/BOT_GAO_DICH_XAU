@echo off
title System Health Check
echo =======================================================
echo Performing Local System Health Check
echo =======================================================

cd /d "%~dp0\.."

python -c "import httpx, json, sys; res = httpx.get('http://127.0.0.1:8000/api/v1/health', timeout=5.0); print(json.dumps(res.json(), indent=2))" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend is unreachable at http://127.0.0.1:8000/api/v1/health.
    echo Please ensure start-backend.bat is running.
)

pause
