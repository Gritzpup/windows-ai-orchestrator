#!/bin/bash

usage() {
    echo "Usage: model-orch.sh <command>"
    echo "  status     - Show current GPU status"
    echo "  ollama     - Switch to Ollama"
    echo "  bonsai-17  - Switch to Bonsai 1.7B"
    echo "  bonsai-8b  - Switch to Bonsai 8B"
    echo "  stop       - Stop all GPU models"
    echo "  comfyui    - Stop GPU models (for ComfyUI)"
    echo "  is-gpu-free - Check if GPU is free"
    echo "  comfyui-running - Check if ComfyUI is running on 8188"
}

check_gpu_free() {
    local gpus=$(nvidia-smi --query-compute-apps=pid,name --format=csv,noheader 2>/dev/null | grep -v "No running" | wc -l)
    [ "$gpus" -gt 0 ] && return 1 || return 0
}

stop_all_gpu() {
    echo "[INFO] Stopping all GPU processes..."
    systemctl --user stop ollama 2>/dev/null
    pkill -f "llama-server" 2>/dev/null
    for i in {1..20}; do
        check_gpu_free && echo "[INFO] GPU freed" && return 0
        sleep 1
    done
    echo "[WARN] GPU may still be in use"
}

case "$1" in
    status)
        echo "=== GPU Status ==="
        nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
        echo ""
        echo "=== GPU Processes ==="
        nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader 2>/dev/null || echo "None"
        echo ""
        echo "=== ComfyUI (8188) ==="
        curl -s --connect-timeout 2 http://localhost:8188/system_stats >/dev/null 2>&1 && echo "Running" || echo "Not running"
        echo ""
        echo "=== LLM Ports ==="
        ss -tlnp | grep -E "8082|8080|11434" || echo "No LLM servers"
        ;;
    stop)
        stop_all_gpu
        ;;
    comfyui)
        echo "[INFO] Switching to ComfyUI mode..."
        stop_all_gpu
        echo "[INFO] GPU is now free for ComfyUI (port 8188)"
        ;;
    is-gpu-free)
        check_gpu_free && exit 0 || exit 1
        ;;
    comfyui-running)
        curl -s --connect-timeout 1 http://localhost:8188/system_stats >/dev/null 2>&1 && exit 0 || exit 1
        ;;
    ollama)
        stop_all_gpu
        echo "[INFO] Starting Ollama..."
        systemctl --user start ollama 2>/dev/null || sudo systemctl --user start ollama 2>/dev/null || echo "[WARN] Could not start ollama"
        sleep 3
        echo "[INFO] Ollama ready on port 11434"
        ;;
    bonsai-17)
        stop_all_gpu
        echo "[INFO] Starting Bonsai 1.7B..."
        tmux kill-session -t bonsai-8082 2>/dev/null
        tmux new-session -d -s bonsai-8082 "cd ~ && ./llama-server --model /home/joshua/models/Bonsai-1.7B-Q1.gguf -ngl 99 --host 0.0.0.0 --port 8082 --ctx-size 32768 --jinja"
        sleep 10
        echo "[INFO] Bonsai 1.7B ready on port 8082"
        ;;
    bonsai-8b)
        stop_all_gpu
        echo "[INFO] Starting Bonsai 8B..."
        tmux kill-session -t bonsai-8080 2>/dev/null
        tmux new-session -d -s bonsai-8080 "cd ~ && ./llama-server --model /home/joshua/models/Bonsai-8B.gguf -ngl 99 --host 0.0.0.0 --port 8080 --ctx-size 32768 --jinja"
        sleep 15
        echo "[INFO] Bonsai 8B ready on port 8080"
        ;;
    *)
        usage
        ;;
esac
