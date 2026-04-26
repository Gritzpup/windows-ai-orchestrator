"""
Windows AI Proxy - port 9000
Routes Ollama requests to WSL, auto-resizes large vision images.
Silent: uses CREATE_NO_WINDOW to suppress all subprocess windows.
"""
import subprocess, json, base64, os, tempfile, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

COMFYUI_PYW = r'C:\Users\Joshua\AppData\Roaming\StabilityMatrix\Packages\ComfyUI\venv\Scripts\python.exe'
MAX_VISION = 50_000  # bytes - resize images larger
CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def curl_wsl(url, data=None):
    """Call WSL Ollama silently. Pass body via Windows temp file."""
    tmp_win = None
    try:
        if data:
            tmp_win = os.path.join(
                os.environ.get('TEMP', r'C:\Users\Joshua\AppData\Local\Temp'),
                f'proxy_req_{os.getpid()}.json'
            )
            with open(tmp_win, 'w', encoding='utf-8') as f:
                f.write(data)
            # Windows path -> WSL path: C:\Users\... -> /mnt/c/Users/...
            wsl_path = tmp_win.replace('\\', '/').replace('C:', '/mnt/c')
            bash_cmd = (
                'curl -s --max-time 900 -X POST '
                '-H "Content-Type: application/json" '
                f'-d @{wsl_path} '
                f'http://localhost:11434{url}'
            )
            cmd = ['wsl', '-e', 'bash', '-c', bash_cmd]
        else:
            bash_cmd = f'curl -s --max-time 900 http://localhost:11434{url}'
            cmd = ['wsl', '-e', 'bash', '-c', bash_cmd]

        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=920,
            creationflags=CREATE_NO_WINDOW
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None
    finally:
        if tmp_win:
            try:
                os.unlink(tmp_win)
            except Exception:
                pass


def resize_image(image_bytes, max_px=200):
    """Resize image via ComfyUI PIL silently. Returns resized bytes or None."""
    tmp_in = tmp_out = None
    try:
        tmp_in = tempfile.mktemp(suffix='.png')
        tmp_out = tempfile.mktemp(suffix='.png')
        with open(tmp_in, 'wb') as f:
            f.write(image_bytes)
        subprocess.run(
            [COMFYUI_PYW, '-c',
             f'from PIL import Image; img=Image.open(r"{tmp_in}"); img.thumbnail(({max_px},{max_px})); img.save(r"{tmp_out}")'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
            creationflags=CREATE_NO_WINDOW
        )
        if os.path.exists(tmp_out):
            with open(tmp_out, 'rb') as f:
                data = f.read()
            return data
    except Exception:
        pass
    finally:
        for f in (tmp_in, tmp_out):
            if f:
                try:
                    os.unlink(f)
                except Exception:
                    pass
    return None


def preprocess(body_str):
    """Auto-resize images >50KB in vision requests."""
    try:
        data = json.loads(body_str)
        changed = False
        for msg in data.get('messages', []):
            content = msg.get('content', [])
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get('type') != 'image_url':
                    continue
                url = item.get('image_url', {}).get('url', '')
                if not (url.startswith('data:image/') and ';base64,' in url):
                    continue
                try:
                    b64 = url.split(';base64,', 1)[1]
                    img_bytes = base64.b64decode(b64)
                    if len(img_bytes) > MAX_VISION:
                        resized = resize_image(img_bytes)
                        if resized and len(resized) < len(img_bytes):
                            item['image_url']['url'] = (
                                url.split(';base64,')[0] + ';base64,' +
                                base64.b64encode(resized).decode()
                            )
                            changed = True
                except Exception:
                    pass
        return json.dumps(data, ensure_ascii=False) if changed else body_str
    except Exception:
        return body_str


class Handler(BaseHTTPRequestHandler):
    def send_json(self, body, status=200):
        b = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def send_text(self, body, status=502):
        b = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == '/v1/ollama-ready':
            resp = curl_wsl('/api/tags')
            self.send_json({'status': 'ok' if resp else 'down'},
                          200 if resp else 503)
        elif self.path == '/v1/queue-status':
            self.send_json({'status': 'ok'})
        elif self.path == '/v1/models':
            resp = curl_wsl('/v1/models')
            if resp:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp.encode())
            else:
                self.send_text('Ollama unavailable', 502)
        else:
            self.send_text('Not found', 404)

    def do_POST(self):
        if not self.path.startswith('/v1/'):
            self.send_text('Not found', 404)
            return

        cl = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(cl)
        body_str = preprocess(body.decode('utf-8', errors='replace'))

        resp = curl_wsl(self.path, data=body_str)
        if resp:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp.encode())
        else:
            self.send_text('Ollama unavailable', 502)

    def log_message(self, fmt, *args):
        pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    print('Proxy: 9000 -> WSL Ollama  |  vision auto-resize enabled')
    try:
        ThreadedHTTPServer(('0.0.0.0', 9000), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
