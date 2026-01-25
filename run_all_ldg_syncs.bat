@echo off
REM Level Data Grow - All Syncs
REM Runs both Action Steps and Meetings syncs
REM Scheduled to run daily at 6:00 AM

cd /d "%~dp0"

echo ============================================
echo LDG All Syncs - %date% %time%
echo ============================================

echo.
echo [1/2] Syncing Action Steps...
echo --------------------------------------------
python ldg_action_steps_sync.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Action Steps sync failed!
) else (
    echo Action Steps sync completed.
)

echo.
echo [2/2] Syncing Meetings...
echo --------------------------------------------
python ldg_meetings_sync.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Meetings sync failed!
) else (
    echo Meetings sync completed.
)

echo.
echo ============================================
echo All syncs finished at %time%
echo ============================================
