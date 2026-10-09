@echo off
title Install NSSM Windows Services - 24/7 Production Deployment
echo =======================================================
echo Installing NSSM Windows Services for XAUUSD Trading Bot
echo 24/7 Resilient Operation Configuration
echo =======================================================

:: Customize base directory if installed elsewhere (e.g. C:\tradebot)
set APP_ROOT=C:\tradebot
set PYTHON_EXE=C:\Python310\python.exe

if not exist "%APP_ROOT%" (
    echo [WARNING] Default %APP_ROOT% does not exist. Using current directory: %~dp0\..\..
    set "APP_ROOT=%~dp0\..\.."
)

echo App Root: %APP_ROOT%
echo Python: %PYTHON_EXE%

:: 1. Backend Service
echo Installing XAUUSD_Backend service...
nssm stop XAUUSD_Backend 2>nul
nssm remove XAUUSD_Backend confirm 2>nul

nssm install XAUUSD_Backend "%PYTHON_EXE%" "-m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"
nssm set XAUUSD_Backend AppDirectory "%APP_ROOT%"
nssm set XAUUSD_Backend Start SERVICE_AUTO_START

:: Crash Recovery: Linear backoff to prevent tight crash loops
nssm set XAUUSD_Backend AppRestartDelay 5000
nssm set XAUUSD_Backend AppThrottle 15000

:: Logging stdout & stderr
if not exist "%APP_ROOT%\logs" mkdir "%APP_ROOT%\logs"
nssm set XAUUSD_Backend AppStdout "%APP_ROOT%\logs\backend_service_stdout.log"
nssm set XAUUSD_Backend AppStderr "%APP_ROOT%\logs\backend_service_stderr.log"
nssm set XAUUSD_Backend AppRotateFiles 1
nssm set XAUUSD_Backend AppRotateBytes 20971520

:: 2. Start Service
echo Starting XAUUSD_Backend service...
nssm start XAUUSD_Backend

echo =======================================================
echo [SUCCESS] Windows Service configured and started.
echo Service status:
nssm status XAUUSD_Backend
echo =======================================================
pause
