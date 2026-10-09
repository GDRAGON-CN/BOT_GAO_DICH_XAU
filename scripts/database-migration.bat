@echo off
title Database Migration - Alembic
echo =======================================================
echo Executing Database Migrations (MySQL 8+)
echo =======================================================

cd /d "%~dp0\..\backend"

echo Applying Alembic migrations to head...
python -m alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Database migrations completed successfully.
) else (
    echo [ERROR] Migration failed. Please check MySQL connection parameters in .env.
)

pause
