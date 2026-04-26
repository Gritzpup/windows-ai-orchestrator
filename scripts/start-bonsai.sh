#!/bin/bash
# Bonsai-8B llama-server launcher (WSL Ubuntu, user: joshua, RTX 2080 SUPER / SM 7.5)
set -euo pipefail

BIN_DIR=/home/joshua/bonsai/bin
LLAMA_BIN="$BIN_DIR/llama-server"
MODEL=/home/joshua/models/Bonsai-8B.gguf
LOG=/tmp/bonsai_server.log

export LD_LIBRARY_PATH="$BIN_DIR:${LD_LIBRARY_PATH:-}"

pkill -f llama-server 2>/dev/null || true
sleep 1

nohup "$LLAMA_BIN" \
    -m "$MODEL" \
    --host 0.0.0.0 --port 8080 \
    -ngl 99 \
    --flash-attn auto \
    --ctx-size 8192 \
    --jinja \
    --temp 0.5 --top-p 0.85 --top-k 20 \
    > "$LOG" 2>&1 &

echo "llama-server PID=$! (log: $LOG)"
echo "Endpoint: http://localhost:8080/v1"
