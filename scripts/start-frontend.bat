@echo off
title Gold Trading Bot - React Frontend Dashboard
echo =======================================================
echo Starting Personal Trading Dashboard (Vite + React)
echo =======================================================

cd /d "%~dp0\..\frontend"

echo Launching local development server on http://localhost:5173 ...
npm run dev
pause
