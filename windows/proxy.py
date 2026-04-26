from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, time, re, base64
from socketserver import ThreadingMixIn

OLLAMA_WSL_CMD = ['wsl', 'curl', '-s', '--max-time', '900']
COMFYUI_PY = r'C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Packages\ComfyUI\venv\Scripts\python.exe'
RESIZE_SCRIPT = r'C:\Users\Joshua\resize_vision.py'

def resize_image(image_data, max_size=200):
    """Resize image using ComfyUI venv PIL, return base64 of resized image."""
    try:
        import struct, tempfile, os
        # Write original image to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False, mode='wb') as f:
            f.write(image_data)
            tmp_in = f.name
        tmp_out = tmp_in.replace('.png', '_resized.png')
        
        # Use PIL to resize
        r = subprocess.run(
            [COMFYUI_PY, '-c',
             f'from PIL import Image; img=Image.open(r"{tmp_in}"); img.thumbnail(({max_size},{max_size})); img.save(r"{tmp_out}")'],
            capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp_in)
        if r.returncode != 0 or not os.path.exists(tmp_out):
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)
            return None, image_data  # fallback to original
        
        with open(tmp_out, 'rb') as f:
            resized = f.read()
        os.unlink(tmp_out)
        return resized, image_data
    except Exception as e:
        return None, image_data

def preprocess_vision_request(body_str):
    """Find and resize large images in vision requests. Return modified body_str."""
    try:
        data = json.loads(body_str)
        modified = False
        
        def process_content(content):
            nonlocal modified
            if isinstance(content, list):
                new_content = []
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        url = item.get('image_url', {}).get('url', '')
                        if url.startswith('data:image/') and ';base64,' in url:
                            b64_data = url.split(';base64,', 1)[1]
                            try:
                                img_bytes = base64.b64decode(b64_data)
                                # Check if image is large (rough size check)
                                if len(img_bytes) > 50000:  # > ~50KB likely too large
                                    resized, _ = resize_image(img_bytes)
                                    if resized and len(resized) < len(img_bytes):
                                        mime = url.split(';base64,')[0] + ';base64,'
                                        item['image_url']['url'] = mime + base64.b64encode(resized).decode()
                                        modified = True
                                        print(f'[proxy] Resized image {len(img_bytes)} -> {len(resized)} bytes')
                            except Exception as e:
                                pass  # keep original
                    new_content.append(process_content(item))
                return new_content
            elif isinstance(content, dict):
                return {k: process_content(v) for k, v in content.items()}
            return content
        
        # Only process chat completion requests with images
        if 'messages' in data:
            for msg in data.get('messages', []):
                if isinstance(msg.get('content'), list):
                    msg['content'] = process_content(msg['content'])
        
        if modified:
            return json.dumps(data, ensure_ascii=False)
        return body_str
    except Exception:
        return body_str

def curl_wsl(url, data=None, headers=None):
    cmd = OLLAMA_WSL_CMD + [url]
    if data:
        cmd += ['-X', 'POST', '-H', 'Content-Type: application/json', '-d', data]
    if headers:
        for k, v in headers.items():
            if k.lower() not in ('host', 'content-length'):
                cmd += ['-H', f'{k}: {v}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=910)
        if result.returncode == 0:
            return result.stdout
        return None
    except:
        return None

def is_llm_running():
    try:
        r = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,name', '--format=csv,noheader'],
                          capture_output=True, text=True, timeout=5)
        return any('llama-server' in l for l in r.stdout.strip().split('\n') if l)
    except:
        return False

def is_comfyui_active():
    try:
        r = subprocess.run(['curl', '-s', '--connect-timeout', '2',
                          'http://localhost:8188/queue'],
                          capture_output=True, text=True, timeout=4)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return len(data.get('queue_running', [])) > 0 or len(data.get('queue_pending', [])) > 0
        return False
    except:
        return False

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/v1/queue-status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            resp = {'gpu_free': not is_llm_running(), 'comfyui_active': is_comfyui_active()}
            self.wfile.write(json.dumps(resp).encode())
        elif self.path == '/v1/models':
            resp = curl_wsl('http://localhost:11434/v1/models')
            if resp:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp.encode())
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'WSL Ollama unavailable')
        elif self.path == '/v1/ollama-ready':
            # Health check for Ollama
            resp = curl_wsl('http://localhost:11434/api/tags')
            if resp:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Ollama unavailable')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/v1/chat/completions'):
            # Wait for ComfyUI to be free
            while is_comfyui_active():
                time.sleep(2)
            while is_llm_running():
                time.sleep(2)

            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl)
            body_str = body.decode('utf-8', errors='replace')

            # Pre-process vision requests (resize large images)
            body_str = preprocess_vision_request(body_str)

            # Forward via WSL curl
            url = 'http://localhost:11434/v1/chat/completions'
            resp = curl_wsl(url, data=body_str)

            if resp:
                try:
                    resp_json = json.loads(resp)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', len(json.dumps(resp_json).encode()))
                    self.end_headers()
                    self.wfile.write(json.dumps(resp_json).encode())
                except:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Content-Length', len(resp))
                    self.end_headers()
                    self.wfile.write(resp.encode())
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'WSL Ollama unavailable')

        elif self.path.startswith('/v1/'):
            # Other v1 routes (embeddings, etc.)
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl)
            url = 'http://localhost:11434/v1/' + self.path[4:]
            resp = curl_wsl(url, data=body.decode('utf-8', errors='replace'))
            if resp:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp.encode())
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'WSL Ollama unavailable')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        # Suppress log noise - print important stuff only
        if 'resize' in str(args) or 'vision' in str(args):
            print(args[0] % args[1:])

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

print('Proxy on 9000 -> WSL Ollama (with vision image resizing)')
ThreadedHTTPServer(('0.0.0.0', 9000), Handler).serve_forever()
