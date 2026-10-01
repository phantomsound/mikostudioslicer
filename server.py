import http.server
import socketserver
import socket
import os
import sys
import json
import tempfile
import webbrowser
import urllib.request

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PORT_FILE = os.path.join(tempfile.gettempdir(), "mikostudioslicer.port")
START_PORT = 8088
MAX_PORT = 8138

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
            self.wfile.write(json.dumps({"app": "MikoStudioSlicer", "status": "online"}).encode("utf-8"))
            return
        super().do_GET()

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
