@echo off
REM Level Data Grow Meetings Sync Script
REM Run this script manually or schedule it with Task Scheduler

cd /d "%~dp0"

echo ============================================
echo LDG Meetings Sync - %date% %time%
echo ============================================

python ldg_meetings_sync.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Sync failed with exit code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Sync completed successfully!
