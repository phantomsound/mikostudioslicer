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


def _decode_image(data_url):
    """Decode a data-URL to a PIL RGBA Image."""
    from PIL import Image
    return Image.open(io.BytesIO(base64.b64decode(data_url.split(",", 1)[-1]))).convert("RGBA")


# ---------------------------------------------------------------------------
#  /api/ai_segment  –  Neural background removal (rembg / u2net)
# ---------------------------------------------------------------------------

def segment(data_url, mode):
    import numpy as np
    from rembg import remove
    from scipy import ndimage as ndi
    img = _decode_image(data_url)
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
        from PIL import Image
        ys, xs = np.where(c)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        piece = arr.copy()
        piece[~c] = 0
        crop = Image.fromarray(piece[y0:y1, x0:x1], "RGBA")
        layers.append({"name": f"{'Piece' if mode == 'split' else 'Cutout'} {i}",
                       "png": png_url(crop), "x": int(x0), "y": int(y0),
                       "w": int(x1 - x0), "h": int(y1 - y0)})
    return layers


# ---------------------------------------------------------------------------
#  /api/vectorize  –  Raster → SVG <path> decomposition (vtracer)
# ---------------------------------------------------------------------------

def vectorize(data_url):
    """Decompose a raster image into clean SVG paths by pre-masking with rembg
    so vtracer only traces true foreground artwork (no background junk)."""
    import vtracer
    from rembg import remove

    img = _decode_image(data_url)

    # --- Pre-mask: strip background so vtracer ignores it entirely ---
    masked = remove(img, session=session()).convert("RGBA")

    # vtracer requires both an input image path AND an output SVG path
    fd_in, in_path = tempfile.mkstemp(suffix=".png")
    fd_out, out_path = tempfile.mkstemp(suffix=".svg")
    try:
        os.close(fd_in)
        os.close(fd_out)
        masked.save(in_path, "PNG")
        vtracer.convert_image_to_svg_py(
            in_path,
            out_path,
            colormode="color",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=16,
            color_precision=6,
            layer_difference=20,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3,
        )
        with open(out_path, "r", encoding="utf-8") as f:
            svg_str = f.read()
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    return {"success": True, "svg": svg_str}


# ---------------------------------------------------------------------------
#  /api/ocr  –  Optical character recognition (pytesseract)
# ---------------------------------------------------------------------------

def ocr(data_url):
    """Extract text with preprocessing to handle multi-colour lettering."""
    import numpy as np
    import pytesseract
    from PIL import ImageEnhance, ImageOps

    img = _decode_image(data_url).convert("RGB")

    # Auto-detect Tesseract binary on Windows
    if sys.platform == "win32":
        for p in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(ROOT, "tesseract", "tesseract.exe"),
        ]:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break

    # --- Preprocessing: 2× upscale + contrast boost so coloured letters survive ---
    from PIL import Image as PILImage
    w, h = img.size
    _lanczos = getattr(PILImage, 'Resampling', PILImage).LANCZOS
    img_up = img.resize((w * 2, h * 2), resample=_lanczos)
    img_up = ImageEnhance.Contrast(img_up).enhance(2.5)
    img_up = ImageOps.autocontrast(img_up)

    arr = np.array(img)

    # Run Tesseract with tuned engine settings
    custom_config = "--oem 3 --psm 6"
    data = pytesseract.image_to_data(img_up, config=custom_config,
                                     output_type=pytesseract.Output.DICT)

    # Group recognised words into lines
    n = len(data["text"])
    lines: dict = {}
    for i in range(n):
        conf = int(data["conf"][i])
        text = data["text"][i].strip()
        if conf < 30 or not text:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if key not in lines:
            lines[key] = {"words": [], "x": 999999, "y": 999999, "x2": 0, "y2": 0}
        ld = lines[key]
        ld["words"].append(text)
        # Coordinates are in 2× space — scale back to original
        lx = data["left"][i] // 2
        ly = data["top"][i] // 2
        lw = data["width"][i] // 2
        lh = data["height"][i] // 2
        ld["x"] = min(ld["x"], lx)
        ld["y"] = min(ld["y"], ly)
        ld["x2"] = max(ld["x2"], lx + lw)
        ld["y2"] = max(ld["y2"], ly + lh)

    # Concatenate all lines into a single text result
    all_lines = []
    best_h = 0
    for key in sorted(lines.keys()):
        ld = lines[key]
        all_lines.append(" ".join(ld["words"]))
        best_h = max(best_h, ld["y2"] - ld["y"])

    full_text = " ".join(all_lines).strip()
    if not full_text:
        return {"success": False, "text": "", "fontSize": 72, "fill": "#000000"}

    fontSize = max(12, int(best_h * 0.85))

    # Sample dominant text colour from the first line's bounding region
    first_ld = lines[sorted(lines.keys())[0]]
    x1c = max(0, first_ld["x"])
    y1c = max(0, first_ld["y"])
    x2c = min(arr.shape[1], first_ld["x2"])
    y2c = min(arr.shape[0], first_ld["y2"])
    region = arr[y1c:y2c, x1c:x2c]
    if region.size > 0:
        gray = np.mean(region, axis=2)
        med = np.median(gray)
        if med > 127:
            mask = gray < med * 0.7
        else:
            mask = gray > med * 1.3 + 30
        if mask.any():
            clr = region[mask].mean(axis=0).astype(int)
        else:
            clr = region.mean(axis=(0, 1)).astype(int)
        fill = f"#{int(clr[0]):02x}{int(clr[1]):02x}{int(clr[2]):02x}"
    else:
        fill = "#000000"

    return {"success": True, "text": full_text, "fontSize": fontSize, "fill": fill}


# ---------------------------------------------------------------------------
#  HTTP handler
# ---------------------------------------------------------------------------

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
        path = self.path.split("?")[0]
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception as e:
            return self.send_json({"error": f"Bad request: {e}"}, 400)
        try:
            if path == "/api/ai_segment":
                mode = body.get("mode", "cutout")
                return self.send_json({"layers": segment(body["image"],
                                       "split" if mode == "split" else "cutout")})
            if path == "/api/vectorize":
                return self.send_json(vectorize(body["image"]))
            if path == "/api/ocr":
                return self.send_json(ocr(body["image"]))
            self.send_json({"error": "not found"}, 404)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)


# ---------------------------------------------------------------------------
#  Server bootstrap
# ---------------------------------------------------------------------------

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
