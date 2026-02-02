@echo off
echo ============================================================
echo SR2/PMAP2 Dashboard Updater
echo ============================================================
echo.

REM Update the dashboard with fresh BigQuery data
echo [1/2] Querying BigQuery for latest data...
C:\Users\sshirey\AppData\Local\Programs\Python\Python312\python.exe update_dashboard_simple.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to update dashboard data
    pause
    exit /b 1
)

echo.
echo [2/2] Deploying to shared drive...

REM TODO: Update this path to your actual shared network drive location
REM Example: set SHARED_PATH=\\your-server\shared-folder\SR2_PMAP2_Dashboard.html
set SHARED_PATH=CHANGE_THIS_TO_YOUR_NETWORK_PATH

REM Check if shared path is configured
if "%SHARED_PATH%"=="CHANGE_THIS_TO_YOUR_NETWORK_PATH" (
    echo.
    echo WARNING: Shared network path not configured!
    echo Please edit this batch file and set SHARED_PATH to your network location.
    echo.
    echo For now, the dashboard has been updated locally at:
    echo %~dp0index.html
    echo.
    echo You can manually copy it to your shared drive.
    pause
    exit /b 0
)

REM Copy to shared drive
copy /Y "%~dp0index.html" "%SHARED_PATH%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Dashboard deployed to:
    echo %SHARED_PATH%
    echo ============================================================
    echo.
    echo Users can now refresh their browsers to see the updated data.
) else (
    echo.
    echo Error: Failed to copy to shared drive
    echo Please check that the path exists and you have write permissions.
)

echo.
pause
