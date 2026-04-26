# Start all services on boot
$ErrorActionPreference = "SilentlyContinue"

# 1. Start Ollama on WSL with 0.0.0.0 binding
Write-Host "Starting WSL Ollama..."
Start-Process -FilePath "wsl.exe" -ArgumentList "-e", "bash", "-c", "OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &" -WindowStyle Hidden

# 2. Start ComfyUI
Write-Host "Starting ComfyUI..."
Start-Process "C:\StabilityMatrix\StabilityMatrix.exe"

# 3. Start proxy
Start-Sleep 5
Write-Host "Starting proxy on 9000..."
Start-Process -FilePath "C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Assets\Python\cpython-3.12.10-windows-x86_64-none\python.exe" -ArgumentList "C:\Users\Joshua\proxy.py" -WindowStyle Hidden

Write-Host "All services started!"
Write-Host ""
Write-Host "Check status:"
Write-Host "  ComfyUI: http://localhost:8188"
Write-Host "  Proxy:  http://localhost:9000"
Write-Host "  Ollama:  via proxy -> WSL Ollama"
