# Model Orchestrator

Script: `~/model-orch.sh` (WSL bash)

## Usage
```bash
~/model-orch.sh ollama      # Use Ollama (phi4-mini, qwen2.5, etc.)
~/model-orch.sh bonsai-17   # Use Bonsai 1.7B Q1
~/model-orch.sh bonsai-8b   # Use Bonsai 8B Q2
~/model-orch.sh status      # Show what's running + GPU memory
~/model-orch.sh stop        # Kill all GPU processes
```

## How it works
- Only one GPU model runs at a time (8GB VRAM on RTX 2080 Super)
- Switching ALWAYS kills other GPU processes first
- Bonsai servers run in tmux sessions for persistence
- Ollama model unloaded via API before killing runners
- Portproxy updated for Windows access

## Endpoints
- Ollama: `http://172.24.144.157:11434/v1`
- Bonsai 1.7B: `http://172.24.144.157:8082/v1`
- Bonsai 8B: `http://172.24.144.157:8080/v1`

## pi models.json (updated)
```json
"ollama": { "baseUrl": "http://172.24.144.157:11434/v1" }
"bonsai-17": { "baseUrl": "http://172.24.144.157:8082/v1" }
"bonsai-8b": { "baseUrl": "http://172.24.144.157:8080/v1" }
```

## Known issues
- Ollama port shows as "RUN" even when no model loaded (just the server)
- GPU memory shows ~1GB reserved even when all models unloaded

## Tested and working
- ✅ Ollama with qwen2.5:1.5b
- ✅ Bonsai 1.7B Q1
- ✅ Bonsai 8B Q2
- ✅ GPU properly freed when switching

## Env file
`C:/Users/Joshua/.pi/orchestrator.env`
