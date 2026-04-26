# Run as admin to set up proxy auto-start on boot via Task Scheduler
$ErrorActionPreference = "Stop"

$PYW = "C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Assets\Python\cpython-3.12.10-windows-x86_64-none\pythonw.exe"
$PROXY = "C:\Users\Joshua\proxy.py"
$TASK = "WindowsAIProxy"

Write-Host "Setting up $TASK to run on boot..."

# Remove existing task
schtasks /Delete /TN $TASK /F 2>$null

# Create new task
$action = New-ScheduledTaskAction -Execute $PYW -Argument "`"$PROXY`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TASK -Action $action -Trigger $trigger -Settings $settings -Description "Windows AI Proxy - routes Ollama via WSL with vision auto-resize" | Out-Null

Write-Host "Done. Proxy will start on login (PID visible in Task Manager)."
Write-Host "To check: Start-Process http://localhost:9000/v1/ollama-ready"
Write-Host "To stop: Get-ScheduledTask $TASK | Unregister-ScheduledTask -Confirm:`$false"
