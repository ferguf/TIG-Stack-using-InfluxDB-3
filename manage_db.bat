@echo off
set BACKUP_DIR=psql\backup
cls

:menu
echo ======================================================
echo           NETWORK DATABASE MANAGEMENT MENU
echo ======================================================
echo 1. RUN BACKUP
echo 2. LIST ALL BACKUP FILES
echo 3. RESTORE FROM A BACKUP
echo 4. EXIT
echo ======================================================
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto backup
if "%choice%"=="2" goto list
if "%choice%"=="3" goto restore
if "%choice%"=="4" exit
goto menu

:backup
echo.
powershell -ExecutionPolicy Bypass -File .\postgres-auto-backup.ps1
pause
goto menu

:list
echo.
echo Available Backups:
dir %BACKUP_DIR%\*.sql /B /O-D
echo.
pause
goto menu

:restore
echo.
echo Available files to copy/paste:
dir %BACKUP_DIR%\*.sql /B /O-D
echo.
set /p filename="Copy and Paste the filename from above: "

if "%filename%"=="" (
    echo ERROR: No filename entered.
    pause
    goto menu
)

if exist %BACKUP_DIR%\%filename% (
    echo.
    echo Restoring %filename%...
    powershell -Command "Get-Content .\%BACKUP_DIR%\%filename% | docker exec -i db psql -U myuser -d mydatabase"
    echo Restore Complete.
) else (
    echo.
    echo ERROR: File '%filename%' not found in %BACKUP_DIR%
)
pause
goto menu
