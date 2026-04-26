# Set up proxy auto-start on login via Task Scheduler
$ErrorActionPreference = "SilentlyContinue"

$PYW = "C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Assets\Python\cpython-3.12.10-windows-x86_64-none\pythonw.exe"
$PROXY = "C:\Users\Joshua\proxy.py"
$TASK = "WindowsAIProxy"

Write-Host "Setting up $TASK to run on login..."

# Remove existing task
schtasks /Delete /TN $TASK /F 2>$null | Out-Null

# Create task - runs when current user logs in
$cmd = "`"$PYW`" `"$PROXY`""
$result = schtasks /Create /TN $TASK /TR $cmd /SC ONLOGON /RU $env:USERNAME /F 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done. Proxy will start on login (silently, no window)."
    Write-Host "  Check: curl http://localhost:9000/v1/ollama-ready"
    Write-Host "  Stop:  schtasks /Delete /TN $TASK /F"
} else {
    Write-Host "Failed (exit $LASTEXITCODE): $result"
}
