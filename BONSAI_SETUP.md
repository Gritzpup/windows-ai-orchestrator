# Bonsai-8B MLLM Setup Guide (WSL Ubuntu + RTX 2080 SUPER)

## Environment
- **WSL user:** `joshua` (home: `/home/joshua`)
- **GPU:** NVIDIA RTX 2080 SUPER (Turing / Compute Capability 7.5)
- **CUDA:** 12.0 (nvcc at `/usr/bin/nvcc`)

## Model
- **Name:** Bonsai-8B (Qwen3-8B architecture, Q1_0 g128 quant, 1-bit TurboQuant)
- **Path:** `/home/joshua/models/Bonsai-8B.gguf` (~1.1 GB)
- **Source:** https://huggingface.co/prism-ml/Bonsai-8B-gguf

## Engine
- **Fork:** PrismML fork of llama.cpp (ships the Q1_0 CUDA kernels needed by Bonsai)
- **Source tree:** `/root/prism-llama.cpp/` (owned by root, keep as-is)
- **Binaries in use:** copied to `/home/joshua/bonsai/bin/`
  - `llama-server`
  - `libggml-*.so*`
- **Build flags:** `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 -DGGML_CUDA_FA=ON`

## Server Launch
Use `~/start-bonsai.sh` (in Windows home / also copied inside WSL). Flags:

```bash
export LD_LIBRARY_PATH=/home/joshua/bonsai/bin:$LD_LIBRARY_PATH

/home/joshua/bonsai/bin/llama-server \
    -m /home/joshua/models/Bonsai-8B.gguf \
    --host 0.0.0.0 --port 8080 \
    -ngl 99 \
    --flash-attn auto \
    --ctx-size 8192 \
    --jinja \
    --temp 0.5 --top-p 0.85 --top-k 20
```

### Why these flags
- `-ngl 99` — offload every layer to the GPU (RTX 2080S has 8 GB; Bonsai Q1_0 fits easily).
- `--flash-attn auto` — FA is built into the fork for SM 7.5.
- `--jinja` — use the **Qwen3 chat template embedded in the GGUF**. Do **not** pass `--chat-template qwen2` — that was the source of malformed output in the old script.
- Sampling (`temp 0.5`, `top-p 0.85`, `top-k 20`) matches the values published by prism-ml/Bonsai-8B-gguf.
- `--ctx-size 8192` — plenty for chat; bump to 32768 only if needed.

## Network
- Port 8080 is auto-forwarded by WSL2 to the Windows host on localhost.
- To expose to the LAN (e.g. Pi at 192.168.1.x), add a Windows `netsh portproxy` entry — not required for local use.
- **OpenAI-compatible endpoint:** `http://localhost:8080/v1`

## Smoke Test
```bash
python3 /mnt/c/Users/Joshua/test_bonsai.py
```
Expected: a valid JSON object, not mojibake or unterminated text.

## Maintenance
- **Logs:** `/tmp/bonsai_server.log`
- **Stop:** `pkill -f llama-server`
- **Restart:** re-run `~/start-bonsai.sh`
- **Rebuild engine (from root):**
  ```bash
  sudo bash -c 'cd /root/prism-llama.cpp/build && cmake --build . --target llama-server -j $(nproc)'
  sudo cp /root/prism-llama.cpp/build/bin/llama-server \
          /root/prism-llama.cpp/build/bin/libggml-*.so* \
          /home/joshua/bonsai/bin/
  sudo chown -R joshua:joshua /home/joshua/bonsai
  ```

## History of the "malformed output" bug
Previous scripts launched the server with `--chat-template qwen2`. Bonsai-8B is a
**Qwen3** fine-tune and its GGUF ships the correct template internally — forcing
qwen2 corrupts the special-token stream and produces garbled or truncated
completions. Use `--jinja` (or simply omit any `--chat-template` override) to
let the GGUF's embedded template drive formatting.
