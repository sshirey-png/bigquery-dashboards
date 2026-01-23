@echo off
REM Level Data Grow Action Steps Sync - Daily Automation
REM Runs the Python script and logs output

set SCRIPT_DIR=C:\Users\sshirey\bigquery_dashboards
set LOG_DIR=%SCRIPT_DIR%\logs
set LOG_FILE=%LOG_DIR%\ldg_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo LDG Action Steps Sync - Started at %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

REM Run the Python script
python "%SCRIPT_DIR%\ldg_action_steps_sync.py" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Sync completed successfully >> "%LOG_FILE%"
) else (
    echo Sync failed with error code %ERRORLEVEL% >> "%LOG_FILE%"
)

echo ============================================================ >> "%LOG_FILE%"
echo Finished at %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

REM Clean up old log files (keep last 30 days)
forfiles /p "%LOG_DIR%" /m *.log /d -30 /c "cmd /c del @path" 2>nul

exit /b %ERRORLEVEL%
