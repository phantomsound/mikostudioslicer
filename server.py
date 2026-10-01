import http.server
import socketserver
import socket
import os
import sys
import json
import base64
import io
import tempfile
import webbrowser
import urllib.request
from PIL import Image

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PORT_FILE = os.path.join(tempfile.gettempdir(), "mikostudioslicer.port")
START_PORT = 8088
MAX_PORT = 8138

# Lazy-load rembg to keep server startup instantaneous
_rembg_session = None

def get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        try:
            from rembg import new_session
            _rembg_session = new_session("u2net")
        except Exception as e:
            print(f"[WARN] rembg could not be initialized: {e}")
            _rembg_session = False
    return _rembg_session

def is_our_service(port):
    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url, headers={"User-Agent": "MikoProbe"})
        with urllib.request.urlopen(req, timeout=0.6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("app") == "MikoStudioSlicer"
    except Exception:
        return False

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True

def get_target_port():
    if os.path.exists(PORT_FILE):
        try:
            with open(PORT_FILE, "r") as f:
                saved_port = int(f.read().strip())
            if is_our_service(saved_port):
                return saved_port, True
        except Exception:
            pass

    for p in range(START_PORT, MAX_PORT):
        if is_our_service(p):
            return p, True
        if not is_port_in_use(p):
            return p, False

    raise RuntimeError(f"No available ports between {START_PORT} and {MAX_PORT}")

class SlicerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"app": "MikoStudioSlicer", "status": "online", "ai_ready": True}).encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/ai_segment":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                req_data = json.loads(body.decode("utf-8"))
                
                # Base64 in -> AI alpha cutout -> Base64 out
                raw_b64 = req_data["image"].split(",")[-1]
                img_bytes = base64.b64decode(raw_b64)
                src_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

                session = get_rembg_session()
                if session:
                    from rembg import remove
                    out_img = remove(
                        src_img,
                        session=session,
                        alpha_matting=True,
                        alpha_matting_foreground_threshold=240,
                        alpha_matting_background_threshold=15,
                        alpha_matting_erode_size=4
                    )
                else:
                    out_img = src_img

                out_buffer = io.BytesIO()
                out_img.save(out_buffer, format="PNG")
                result_b64 = "data:image/png;base64," + base64.b64encode(out_buffer.getvalue()).decode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "image": result_b64}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return
        super().do_POST()

    def log_message(self, format, *args):
        pass

def main():
    os.chdir(DIRECTORY)
    port, already_running = get_target_port()

    if already_running:
        if "--launch" in sys.argv:
            webbrowser.open(f"http://localhost:{port}")
        sys.exit(0)

    try:
        with open(PORT_FILE, "w") as f:
            f.write(str(port))
    except Exception:
        pass

    if "--launch" in sys.argv:
        webbrowser.open(f"http://localhost:{port}")

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", port), SlicerHandler) as httpd:
            httpd.serve_forever()
    finally:
        if os.path.exists(PORT_FILE):
            try:
                os.remove(PORT_FILE)
            except Exception:
                pass

if __name__ == "__main__":
    main()
