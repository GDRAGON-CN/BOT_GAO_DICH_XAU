@echo off
title Test Webhook & Signal Pipeline
echo =======================================================
echo Testing TradingView Webhook, Risk Engine & Demo Order
echo =======================================================

cd /d "%~dp0\.."

python backend\scripts\test_webhook.py
pause
