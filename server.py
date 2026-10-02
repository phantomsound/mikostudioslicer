import argparse, base64, io, json, os, sys, tempfile, threading, urllib.request, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

APP = "Miko Studio Slicer"
ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("U2NET_HOME", os.path.join(ROOT, "models"))
PORT_FILE = os.path.join(tempfile.gettempdir(), "MikoStudioSlicer.port")
LO, HI = 8088, 8138
_sess, _lock = None, threading.Lock()


def session():
    global _sess
    with _lock:
        if _sess is None:
            from rembg import new_session
            _sess = new_session("u2net")
    return _sess


def png_url(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def segment(data_url, mode):
    import numpy as np
    from PIL import Image
    from rembg import remove
    from scipy import ndimage as ndi
    img = Image.open(io.BytesIO(base64.b64decode(data_url.split(",", 1)[-1]))).convert("RGBA")
    out = remove(img, session=session()).convert("RGBA")
    arr = np.array(out)
    mask = arr[..., 3] > 8
    if not mask.any():
        return []
    if mode == "split":
        grow = max(2, min(img.size) // 120)
        lab, n = ndi.label(ndi.binary_dilation(mask, iterations=grow))
        comps = [(lab == i) & mask for i in range(1, n + 1)]
        floor = mask.size * 0.0005
        comps = sorted((c for c in comps if c.sum() >= floor), key=lambda c: -c.sum())[:64]
    else:
        comps = [mask]
    layers = []
    for i, c in enumerate(comps, 1):
        ys, xs = np.where(c)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        piece = arr.copy()
        piece[~c] = 0
        crop = Image.fromarray(piece[y0:y1, x0:x1], "RGBA")
        layers.append({"name": f"{'Piece' if mode == 'split' else 'Cutout'} {i}",
                       "png": png_url(crop), "x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0)})
    return layers


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/health":
            return self.send_json({"app": APP, "status": "online"})
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/ai_segment":
            return self.send_json({"error": "not found"}, 404)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            mode = body.get("mode", "cutout")
            self.send_json({"layers": segment(body["image"], "split" if mode == "split" else "cutout")})
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)


def probe(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.4) as r:
            return json.load(r).get("app") == APP
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    args = ap.parse_args()
    srv = None
    for port in range(LO, HI + 1):
        if probe(port):
            if args.launch:
                webbrowser.open(f"http://127.0.0.1:{port}/")
            return
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if srv is None:
        sys.exit(1)
    with open(PORT_FILE, "w") as f:
        f.write(str(port))
    threading.Thread(target=session, daemon=True).start()
    if args.launch:
        threading.Timer(0.6, webbrowser.open, [f"http://127.0.0.1:{port}/"]).start()
    try:
        srv.serve_forever()
    finally:
        try:
            os.remove(PORT_FILE)
        except OSError:
            pass


if __name__ == "__main__":
    main()
