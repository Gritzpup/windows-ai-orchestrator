# Windows AI Orchestrator

Local AI coding agent setup: ComfyUI (GPU image/video) + Ollama (chat) + Bonsai on Windows/WSL.

## Architecture

```
User → Port 9000 (proxy) → WSL Ollama (port 11434)
                ↓
         GPU check (nvidia-smi)
         ComfyUI check (port 8188 queue)
```

## Quick Start

```powershell
# 1. Start WSL Ollama
wsl -e bash -c "OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &"

# 2. Start ComfyUI
Start-Process "C:\StabilityMatrix\StabilityMatrix.exe"

# 3. Start proxy
python proxy.py
```

Or use `start_all.ps1` to start everything at once.

## Services

| Service | Port | Location |
|---------|------|----------|
| Proxy | 9000 | Windows (`proxy.py`) |
| ComfyUI | 8188 | Windows (Stability Matrix) |
| Ollama | 11434 | WSL |
| Bonsai 1.7B | 8082 | WSL (llama-server) |
| Bonsai 8B | 8080 | WSL (llama-server) |

## Models

### Ollama (13 models)
- `phi4-mini:latest` - fast coding (2.5GB)
- `qwen2.5vl:7b` - vision model (6GB)
- `qwen3:8b` - general purpose (5.2GB)
- `bonsai-1.7b:latest` / `bonsai-8b:latest` - Bonsai models

### ComfyUI
- **Flux Dev FP8** - image generation (DiffusionModels/flux1-dev/)
- **Wan 2.1 I2V** - image-to-video (DiffusionModels/wan2.1/)
- **CLIP-L, CLIP-Vision-H** - text/vision encoders
- **Wan VAE, SDXL VAE** - decoders

## Proxy Usage

```python
import urllib.request, json

# Text chat
data = {
    "model": "phi4-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
}
req = urllib.request.Request(
    "http://localhost:9000/v1/chat/completions",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read()))

# Vision (resize image first!)
from PIL import Image
img = Image.open("screenshot.png").resize((200, 200))
img.save("temp.png")
# Then send temp.png via vision API
```

## Vision Model (qwen2.5vl:7b)

⚠️ **Image size limit**: Resize to max 200x200 before sending. Large images (screenshot ~260KB) will timeout.

```python
# Resize image before vision request
from PIL import Image
img = Image.open("large.png")
img = img.resize((200, 200))  # Max 200x200
img.save("small.png")
# Now use small.png for vision
```

## ComfyUI API

```python
import urllib.request, json

# Wan I2V workflow
prompt = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "example.png"}},
    "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "Test"}}
}
data = {"prompt": prompt}
req = urllib.request.Request(
    "http://localhost:8188/prompt",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=30) as r:
    result = json.loads(r.read())
    print(result["prompt_id"])
```

### ⚠️ Critical: String Node IDs
Linked inputs **must** use string node IDs:
```python
# WRONG:
{"inputs": {"clip": [2, 0]}}
# CORRECT:
{"inputs": {"clip": ["2", 0]}}
```

## Pi Agent Config

The Pi agent (`~/.pi/`) points to the Windows proxy:
- Ollama: `http://localhost:9000/v1` (all Ollama models)

## Drive Layout

- C: ~80GB free
- WSL VHDX: 77GB
- Ollama blobs: `/usr/share/ollama/.ollama/models/blobs/`
- ComfyUI models: `StabilityMatrix/Models/`

## Troubleshooting

### Proxy returns "WSL Ollama unavailable"
```bash
wsl -e bash -c "curl -s http://localhost:11434/api/tags"
# If empty, restart Ollama:
wsl -e bash -c "pkill -9 ollama; OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &"
```

### Vision model times out
- Resize image to 200x200 max before sending
- Check Ollama is running: `wsl curl -s http://localhost:11434/api/tags`

### ComfyUI /prompt returns 500
- Use string node IDs for linked inputs
- Check ComfyUI log: `ComfyUI/user/comfyui.log`

### WSL network issues
- The proxy uses `wsl curl` forwarding to bypass direct Windows→WSL HTTP
- If Ollama still fails, check WSL: `wsl --shutdown && wsl`

## Vision Resize (Auto-handled by proxy)

The proxy automatically resizes large images before sending to the vision model (qwen2.5vl:7b). Images over ~50KB are resized to max 200x200 using ComfyUI's PIL.

```python
# Just send any image - proxy handles resizing automatically:
data = {
    "model": "qwen2.5vl:7b",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
    ]}]
}
# Proxy auto-resizes large images before forwarding to Ollama
```

## Repo Structure
```
windows-ai-orchestrator/
├── windows/
│   └── proxy.py           # GPU-aware proxy (Windows)
├── wsl/
│   └── model-orch.sh     # GPU model orchestrator (WSL)
├── scripts/
│   ├── start_all.ps1     # Start all services
│   ├── start-bonsai.sh   # Start Bonsai servers
│   └── *.bat             # Windows launcher scripts
├── pi-agent/
│   └── models.json       # Pi agent model config
├── docs/
│   └── STATUS.md         # Full system documentation
├── BONSAI_SETUP.md
└── README.md
```
