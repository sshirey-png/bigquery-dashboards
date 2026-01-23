# Setup Scheduled Task for LDG Action Steps Sync
# Run this script once as Administrator to create the scheduled task

$taskName = "LDG Action Steps Sync"
$scriptPath = "C:\Users\sshirey\bigquery_dashboards\run_ldg_sync.bat"

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create the action
$action = New-ScheduledTaskAction -Execute $scriptPath

# Create the trigger (daily at 6:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

# Create the principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily sync of Level Data Grow action steps to BigQuery"

Write-Host "Scheduled task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "The task will run daily at 6:00 AM" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test the task now, run:" -ForegroundColor Yellow
Write-Host "  schtasks /run /tn `"$taskName`"" -ForegroundColor White
Write-Host ""
Write-Host "To view task status:" -ForegroundColor Yellow
Write-Host "  schtasks /query /tn `"$taskName`"" -ForegroundColor White
