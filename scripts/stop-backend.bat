@echo off
title Stop Gold Trading Bot Backend
echo =======================================================
echo Stopping Gold Trading Bot - Backend Service
echo =======================================================

echo Terminating uvicorn / python backend processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing PID %%a...
    taskkill /F /PID %%a
)

echo Backend stop command executed.
pause
