@echo off
title Database Backup - MySQL Dump
echo =======================================================
echo Exporting MySQL Database Backup (mysqldump)
echo =======================================================

set BACKUP_DIR=%~dp0\..\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "MIN=%dt:~10,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%MIN%"

set BACKUP_FILE=%BACKUP_DIR%\tradebot_db_%TIMESTAMP%.sql

echo Backing up tradebot_db to %BACKUP_FILE% ...
mysqldump -u root -p tradebot_db --single-transaction --quick --lock-tables=false > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backup created at: %BACKUP_FILE%
) else (
    echo [ERROR] mysqldump failed. Ensure mysqldump is in your Windows PATH and credentials are valid.
)

pause
