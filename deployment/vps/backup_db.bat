@echo off
set BACKUP_DIR=C:\backups\tradebot_mysql
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo Backing up tradebot_db database to %BACKUP_DIR%\tradebot_backup_%TIMESTAMP%.sql...
mysqldump -u root -proot --databases tradebot_db > "%BACKUP_DIR%\tradebot_backup_%TIMESTAMP%.sql"

echo Backup completed.
