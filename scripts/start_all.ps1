# Start all AI services silently on boot
$ErrorActionPreference = "SilentlyContinue"

$PYW = "C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Assets\Python\cpython-3.12.10-windows-x86_64-none\pythonw.exe"
$PROXY = "C:\Users\Joshua\proxy.py"

# Kill existing proxy windows
Get-Process -Name "pythonw" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*proxy.py*" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

# 1. WSL Ollama (GPU)
Start-Process -FilePath "wsl.exe" -ArgumentList "-e", "bash", "-c", "OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &" -WindowStyle Hidden

# 2. ComfyUI (GPU)
Start-Process "C:\StabilityMatrix\StabilityMatrix.exe"

# 3. Proxy on 9000 (silent, no window)
Start-Sleep 3
Start-Process -FilePath $PYW -ArgumentList $PROXY -WindowStyle Hidden

Write-Host "All services started silently."
Write-Host "  ComfyUI: http://localhost:8188"
Write-Host "  Proxy:   http://localhost:9000"
