# ComfyUI + Ollama Setup Summary

## Services Running
- **ComfyUI**: localhost:8188 (Stability Matrix v0.19.3, GPU-accelerated)
- **Proxy**: localhost:9000 → WSL Ollama via `wsl curl`
- **WSL Ollama**: running on port 11434, bound to 0.0.0.0

## COMFYUI API (v0.19.3)

### Critical: String Node IDs
Linked inputs MUST use **string node IDs**:
```python
# WRONG (integer IDs):
{"inputs": {"clip": [2, 0]}}

# CORRECT (string IDs):
{"inputs": {"clip": ["2", 0]}}
```

### Workflow Structure
```python
prompt = {
    '1': {'class_type': 'NodeType', 'inputs': {...}},
    '2': {'class_type': 'NodeType', 'inputs': {...}},
}
data = {'prompt': prompt}
# POST to http://localhost:8188/prompt
```

### Error Types
- `prompt_no_outputs` = workflow valid, no output nodes
- `prompt_outputs_failed_validation` = node validation error
- `execution_error` = runtime error (check history endpoint)

### Status Check
```python
import urllib.request, json
# Check queue
r = urllib.request.urlopen('http://localhost:8188/queue', timeout=5)
print(json.loads(r.read()))

# Check history
r = urllib.request.urlopen(f'http://localhost:8188/history/{prompt_id}', timeout=5)
d = json.loads(r.read())
print(d[prompt_id]['status']['status_str'])  # 'success' or 'error'
```

## Wan I2V Workflow (TESTED ✅)
- Wan 2.1 I2V via WanImageToVideo node
- CLIP type: "wan" with T5 XXL text encoder
- Output: animated WEBP video (9 frames = 1 second)
- Generated: `C:/Users/Joshua/AppData/Roaming/StabilityMatrix/Packages/ComfyUI/output/WanTest_00001_.webp`

```python
{
    '2': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'clip-l\\clip_l.safetensors', 'type': 'wan'}},
    '3': {'class_type': 'CLIPTextEncode', 'inputs': {'text': 'prompt', 'clip': ['2', 0]}},
    '4': {'class_type': 'CLIPTextEncode', 'inputs': {'text': 'negative', 'clip': ['2', 0]}},
    '5': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'wan\\wan_2.1_vae.safetensors'}},
    '6': {'class_type': 'CLIPVisionLoader', 'inputs': {'clip_name': 'clip-vit-h\\clip_vision_h.safetensors'}},
    '7': {'class_type': 'LoadImage', 'inputs': {'image': 'example.png'}},
    '8': {'class_type': 'CLIPVisionEncode', 'inputs': {'clip_vision': ['6', 0], 'image': ['7', 0], 'crop': 'center'}},
    '9': {'class_type': 'WanImageToVideo', 'inputs': {
        'positive': ['3', 0], 'negative': ['4', 0], 'vae': ['5', 0],
        'width': 512, 'height': 512, 'length': 9, 'batch_size': 1,
        'clip_vision_output': ['8', 0], 'start_image': ['7', 0]
    }},
    '10': {'class_type': 'VAEDecode', 'inputs': {'samples': ['9', 2], 'vae': ['5', 0]}},
    '11': {'class_type': 'SaveAnimatedWEBP', 'inputs': {'images': ['10', 0], 'fps': 8.0, 'lossless': False, 'quality': 80, 'method': 'default', 'filename_prefix': 'WanTest'}}
}
```

## VISION MODEL (qwen2.5vl:7b via Proxy)

### HOW IT WORKS ✅
- Vision model is accessible through port 9000 proxy
- Small images (< ~10KB base64) work in 5-15 seconds
- Image passed as base64 data URI: `data:image/png;base64,{base64}`

### HOW TO USE
```python
import base64, json, urllib.request

with open('image.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

data = {
    'model': 'qwen2.5vl:7b',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'What is in this image?'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}}
        ]
    }],
    'max_tokens': 100
}

req = urllib.request.Request(
    'http://localhost:9000/v1/chat/completions',
    data=json.dumps(data).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req, timeout=300) as r:
    resp = json.loads(r.read())
    print(resp['choices'][0]['message']['content'])
```

### IMPORTANT: Image Size Limit
- Small images (50x50, ~100 bytes): works in ~10 seconds ✅
- Large images (screenshot ~260KB): **TIMES OUT after 10+ minutes** ❌
- **Recommendation**: Resize images to max ~200x200 before sending for vision

### Test Results
- Tiny 50x50 red PNG → "The image is solid red." ✅
- Screenshot (259KB base64) → **timeout after 638s** ❌
- Solution: resize screenshot before sending to vision model

## Flux Dev FP8 (ISSUES ❌)
- Model file present: `flux1-dev-fp8.safetensors`
- T5 XXL text encoder corrupted: shape mismatch errors on load
- Both `t5xxl_fp8.safetensors` and `umt5_xxl_fp16.safetensors` fail
- Wan pipeline works because it uses CLIP-L with type="wan"

## WSL Ollama Models (13 total)
| Model | Size | Speed | Status |
|-------|------|-------|--------|
| phi4-mini | 2.5GB | Fast | ✅ |
| phi4-mini-reasoning | 3.2GB | Medium | ✅ |
| qwen2.5:7b | 4.7GB | Medium | ✅ |
| qwen2.5vl:7b | 6GB | **Slow** | ✅ vision works |
| qwen3:8b | 5.2GB | Medium | ✅ |
| bonsai-8b | 1.2GB | Fast | ✅ |
| bonsai-1.7b | 248MB | Fast | ✅ |
| deepseek-r1:8b | 5.2GB | Medium | ✅ |
| codeqwen | 4.2GB | Medium | ✅ |
| hermes3:8b-q5_K_M | 5.7GB | Medium | ✅ |
| dolphin3:8b | 4.9GB | Medium | ✅ |
| gemma2:2b | 1.6GB | Fast | ✅ |
| finance-llama-8b | 4.9GB | Medium | ✅ |

## ComfyUI Models Available
- Flux Dev FP8: `Models/DiffusionModels/flux1-dev/flux1-dev-fp8.safetensors` ✅
- Wan 2.1 I2V: `Models/DiffusionModels/wan2.1/wan2.1_i2v_480p_14B_bf16.safetensors` ✅
- SDXL VAE: `Models/VAE/sdxl-vae/sdxl-vae.safetensors` ✅
- Wan VAE: `Models/VAE/wan/wan_2.1_vae.safetensors` ✅
- CLIP-L: `Models/TextEncoders/clip-l/clip_l.safetensors` ✅
- CLIP-Vision-H: `Models/ClipVision/clip-vit-h/clip_vision_h.safetensors` ✅
- T5 XXL: `Models/TextEncoders/t5-xxl/t5-xxl.safetensors` (57MB, config only) ⚠️
- T5 XXL FP8: `Models/TextEncoders/t5-xxl/t5xxl_fp8.safetensors` (4.6GB, corrupted) ❌
- UMT5 XXL: `Models/TextEncoders/umt5-xxl/umt5_xxl_fp16.safetensors` (1.7GB, invalid) ❌
- Pulsar Gay NSFW: `Models/StableDiffusion/pulsarGayNSFW_fp8.safetensors` ✅

## Drive Usage
- C: ~80GB free
- WSL VHDX: 77GB (down from 151.6GB after compaction)

## API Keys
- CivitAI: 2a5baf2767e1f83069609b9df5538bed
- CivitAI 2: 81340f0a0c076b030a7954f13bb5755a

## Known Issues
1. **Flux Dev needs T5 XXL text encoder**: download from HuggingFace `google/flan-t5-xxl`
2. **Vision model slow on large images**: resize to max 200x200 before vision requests
3. **Ollama runner zombies**: `ollama stop <model>` or `pkill -9 ollama` then restart
4. **WSL IP changes**: proxy uses `wsl curl` forwarding to avoid this
5. **WSL VHDX compaction crash**: `wsl --shutdown` to recover
