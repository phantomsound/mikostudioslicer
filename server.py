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
#  Crisp alpha matting (razor-sharp cutout edges)
# ---------------------------------------------------------------------------

def crisp_matte(arr):
    """Refine an RGBA uint8 array from rembg into a razor-sharp silhouette.

    1. Defringe: for transition pixels with 20 <= alpha <= 235, replace RGB
       with the colour of the nearest solid interior pixel (alpha > 235),
       eliminating background colour bleeding into the soft u2net halo.
    2. Threshold clamping: snap transition pixels with alpha >= 128 to 255,
       and drop boundary pixels with alpha < 128 to 0.
    """
    import numpy as np
    from scipy import ndimage as ndi

    arr = arr.copy()
    alpha = arr[..., 3]

    fringe = (alpha >= 20) & (alpha <= 235)
    core = alpha > 235
    if not core.any():
        core = alpha >= 128
    if fringe.any() and core.any():
        _, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
        fy, fx = iy[fringe], ix[fringe]
        arr[..., :3][fringe] = arr[..., :3][fy, fx]

    # Edge threshold clamping: alpha >= 128 -> 255, alpha < 128 -> 0
    arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0).astype(np.uint8)
    arr[arr[..., 3] == 0, :3] = 0
    return arr


# ---------------------------------------------------------------------------
#  /api/ai_segment, /api/cutout  –  Dual-Engine Cutout (Chroma Logo vs AI Photo)
# ---------------------------------------------------------------------------

def dual_engine_cutout(data_url, mode="auto", tolerance=22.0):
    """Intelligent Dual-Engine Cutout:
    - Mode 'auto': Automatically analyzes border pixels. If border is flat
      (border_std < 18.0), uses razor-sharp Euclidean Chroma cutout.
      If busy/photo, uses neural salient object extraction (rembg).
    - Mode 'logo': Forces Chroma logo/text cutout with anti-aliased edge.
    - Mode 'photo': Forces rembg AI neural salient object removal.
    - Mode 'split': Runs dual-engine and splits into connected component layers.
    """
    import numpy as np
    from PIL import Image as PILImage
    from scipy import ndimage as ndi

    img = _decode_image(data_url).convert("RGBA")
    w, h = img.size
    np_img = np.array(img)

    # 1. Sample border pixels (top, bottom, left, right 2px strips)
    border_pixels = np.concatenate([
        np_img[:2, :, :3].reshape(-1, 3),
        np_img[-2:, :, :3].reshape(-1, 3),
        np_img[:, :2, :3].reshape(-1, 3),
        np_img[:, -2:, :3].reshape(-1, 3)
    ])
    border_std = float(np.std(border_pixels, axis=0).mean())
    median_bg = np.median(border_pixels, axis=0)  # [R, G, B]

    is_flat_bg = border_std < 18.0 or mode in ("logo", "stamp")

    if is_flat_bg and mode != "photo":
        # --- CHROMA / FLOOD-FILL LOGO CUTOUT (Razor Sharp for Text/Logos) ---
        rgb = np_img[:, :, :3].astype(np.float32)
        diff = np.sqrt(np.sum((rgb - median_bg) ** 2, axis=2))

        feather = 2.0
        tol = float(tolerance) if tolerance is not None else 22.0
        alpha = np.clip((diff - tol) / feather * 255.0, 0, 255).astype(np.uint8)

        # Enforce pure transparency on borders to prevent outer framing slivers
        alpha[:1, :] = 0; alpha[-1:, :] = 0; alpha[:, :1] = 0; alpha[:, -1:] = 0

        # Preserve existing transparency if image already had alpha
        if np_img.shape[2] == 4:
            alpha = np.minimum(alpha, np_img[:, :, 3])

        out_arr = np.dstack([np_img[:, :, :3], alpha])
        out_arr[alpha == 0, :3] = 0
        out_img = PILImage.fromarray(out_arr, "RGBA")
        engine_used = "chroma_logo"
    else:
        # --- REMBG AI SALIENT OBJECT CUTOUT (For Natural Photos Only) ---
        from rembg import remove
        raw = remove(img, session=session()).convert("RGBA")
        out_img = PILImage.fromarray(crisp_matte(np.array(raw)), "RGBA")
        engine_used = "rembg_photo"

    arr = np.array(out_img)
    mask = arr[..., 3] > 8

    if not mask.any():
        return {
            "success": True,
            "image": png_url(out_img),
            "layers": [],
            "mode": engine_used,
            "border_std": border_std
        }

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
        crop = PILImage.fromarray(piece[y0:y1, x0:x1], "RGBA")
        layers.append({
            "name": f"{'Piece' if mode == 'split' else 'Cutout'} {i}",
            "png": png_url(crop),
            "x": int(x0), "y": int(y0),
            "w": int(x1 - x0), "h": int(y1 - y0)
        })

    return {
        "success": True,
        "image": png_url(out_img),
        "layers": layers,
        "mode": engine_used,
        "border_std": border_std
    }


def segment(data_url, mode="cutout"):
    res = dual_engine_cutout(data_url, mode=mode)
    return res.get("layers", [])


# ---------------------------------------------------------------------------
#  /api/vectorize  –  Raster → SVG <path> decomposition (vtracer)
#  with smart pre-trace enhancement pipeline
# ---------------------------------------------------------------------------

def _sample_border_color(pil_img):
    """Sample the dominant/median border background color of the image.
    Returns (R, G, B) tuple or None if the border is predominantly transparent.
    """
    import numpy as np
    arr = np.array(pil_img)
    if arr.ndim != 3 or arr.shape[0] < 4 or arr.shape[1] < 4:
        return None

    top = arr[:2, :, :]
    bottom = arr[-2:, :, :]
    left = arr[:, :2, :]
    right = arr[:, -2:, :]

    border = np.concatenate([
        top.reshape(-1, arr.shape[2]),
        bottom.reshape(-1, arr.shape[2]),
        left.reshape(-1, arr.shape[2]),
        right.reshape(-1, arr.shape[2])
    ], axis=0)

    if arr.shape[2] == 4:
        alpha = border[:, 3]
        opaque = border[alpha > 40]
        if len(opaque) < 0.20 * len(border):
            return None
        border_rgb = opaque[:, :3]
    else:
        border_rgb = border[:, :3]

    med = np.median(border_rgb, axis=0).astype(int)
    return (int(med[0]), int(med[1]), int(med[2]))


def _preprocess_for_vectorization(pil_img, num_colors=12, bg_color=None):
    """Cleanse raster artwork into solid, crisp colour regions before tracing.

    Pipeline stages:
      A. Neural background cutout  (rembg / u2net)
      B. Hard binary alpha          → eliminates soft edge fringes; purges enclosed bg cavity
      C. Median surface flattening  → removes anti-alias noise
      D. Perceptual saturation-weighted K-Means → preserves vibrant swatches against dark fringe
      E. Re-apply clean alpha mask
    """
    import numpy as np
    from PIL import Image as PILImage, ImageFilter
    from rembg import remove
    import scipy.cluster.vq as vq
    import warnings

    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")

    # --- A: Neural background removal ---
    try:
        cutout = remove(pil_img, session=session()).convert("RGBA")
    except Exception:
        cutout = pil_img

    r, g, b, a = cutout.split()

    # --- B: Hard binarise alpha (>140 → opaque, else transparent) ---
    alpha_np = np.array(a)
    binary_alpha = np.where(alpha_np > 140, 255, 0).astype(np.uint8)

    # Purge interior cavities matching sampled border background color
    if bg_color is not None:
        raw_rgb = np.array(PILImage.merge("RGB", (r, g, b)), dtype=np.float32)
        dist_bg = np.sqrt(np.sum((raw_rgb - np.array(bg_color, dtype=np.float32)) ** 2, axis=2))
        binary_alpha[dist_bg < 18] = 0

    a_clean = PILImage.fromarray(binary_alpha, mode="L")
    clean_rgb = PILImage.merge("RGB", (r, g, b))

    # --- C: Median filter – smooths micro-noise & AA artefacts ---
    smoothed = clean_rgb.filter(ImageFilter.MedianFilter(size=3))
    smoothed_np = np.array(smoothed)
    mask = binary_alpha > 0

    # --- D: Perceptual saturation-weighted K-Means clustering ---
    opaque_pixels = smoothed_np[mask].astype(np.float32)
    if len(opaque_pixels) > 0:
        unique_pixels = np.unique(opaque_pixels, axis=0)
        actual_k = max(1, min(int(num_colors), len(unique_pixels)))
        if len(opaque_pixels) > 30000:
            sample_idx = np.random.choice(len(opaque_pixels), 30000, replace=False)
            sample = opaque_pixels[sample_idx]
        else:
            sample = opaque_pixels

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            centroids, _ = vq.kmeans2(sample, actual_k, minit="points", iter=15)
            labels, _ = vq.vq(opaque_pixels, centroids)

        # For every quantized cluster, weight centroid toward higher saturation
        max_c = np.max(opaque_pixels, axis=1)
        min_c = np.min(opaque_pixels, axis=1)
        sat = np.where(max_c > 0, (max_c - min_c) / np.maximum(max_c, 1e-5), 0.0)
        val = max_c / 255.0
        w = ((sat + 0.05) ** 2) * (val + 0.05)

        for k in range(actual_k):
            m = (labels == k)
            if m.any():
                w_sum = np.sum(w[m])
                if w_sum > 0:
                    centroids[k] = np.sum(opaque_pixels[m] * w[m, None], axis=0) / w_sum
                else:
                    centroids[k] = np.mean(opaque_pixels[m], axis=0)

        quantized_opaque = centroids[labels].clip(0, 255).astype(np.uint8)
        out_rgb = smoothed_np.copy()
        out_rgb[mask] = quantized_opaque
        quantized_rgb = PILImage.fromarray(out_rgb, mode="RGB")
    else:
        quantized_rgb = smoothed

    # --- E: Re-apply clean binary alpha ---
    r_q, g_q, b_q = quantized_rgb.split()
    return PILImage.merge("RGBA", (r_q, g_q, b_q, a_clean))



# Shared tracing geometry tuned for crisp typography & geometric marks.
# Applied to every preset (after the preset's own colour settings).
CRISP_TRACE_PARAMS = dict(
    corner_threshold=40,    # keep sharp corners on letters/badges (default 60 rounds them)
    splice_threshold=45,    # tighter Bezier splice
    length_threshold=3.5,   # shorter segments -> closer curve fit
    filter_speckle=3,       # drop lone micro-artifacts only
)

VECTORIZE_PRESETS = {
    # Flat geometric brand marks and icons
    "logo": {
        "colors": 8,
        "vtracer": dict(colormode="color", hierarchical="stacked",
                        color_precision=6, layer_difference=20),
    },
    # Cartoon artwork, badges, detailed mascots
    "illustration": {
        "colors": 16,
        "vtracer": dict(colormode="color", hierarchical="stacked",
                        color_precision=8, layer_difference=12),
    },
    # Single-colour stamps, typography, ink marks (strict 2-colour mask)
    "silhouette": {
        "colors": 2,
        "vtracer": dict(colormode="binary", hierarchical="cutout"),
    },
}
DEFAULT_PRESET = "logo"
_PRESET_ALIASES = {"stamp": "silhouette", "ink": "silhouette", "stamp_ink": "silhouette"}


def _otsu_threshold(gray_np):
    """Otsu's method on a uint8 grayscale array -> threshold in [0, 255]."""
    import numpy as np
    hist = np.bincount(gray_np.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    sum_all = (np.arange(256) * hist).sum()
    w_b = sum_b = 0.0
    best_t, best_var = 127, -1.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var, best_t = var, t
    return best_t


def _binary_mask_for_vectorization(pil_img):
    """Strict 2-colour mask: solid black ink on opaque white, no greys.

    Ink is whichever side of the Otsu split is NOT the border/background
    colour; images that already carry transparency use their alpha as ink.
    """
    import numpy as np
    from PIL import Image as PILImage

    rgba = np.array(pil_img.convert("RGBA"))
    alpha = rgba[..., 3]
    if (alpha < 128).mean() > 0.05:
        ink = alpha >= 128
    else:
        gray = np.array(pil_img.convert("L"))
        t = _otsu_threshold(gray)
        dark = gray <= t
        border = np.concatenate([dark[0, :], dark[-1, :], dark[:, 0], dark[:, -1]])
        bg_is_dark = border.mean() > 0.5
        ink = ~dark if bg_is_dark else dark
    out = np.where(ink, 0, 255).astype(np.uint8)
    return PILImage.fromarray(out, mode="L").convert("RGB")


def _resolve_preset(preset):
    key = str(preset or DEFAULT_PRESET).strip().lower()
    key = _PRESET_ALIASES.get(key, key)
    return key if key in VECTORIZE_PRESETS else DEFAULT_PRESET


def vectorize(data_url, preset=DEFAULT_PRESET):
    """Decompose a raster image into clean SVG paths via the pre-trace
    enhancement pipeline + vtracer, tuned by ``preset``
    ("logo" | "illustration" | "silhouette")."""
    import vtracer

    preset = _resolve_preset(preset)
    cfg = VECTORIZE_PRESETS[preset]

    img = _decode_image(data_url)
    bg_color = _sample_border_color(img)

    # Run the preset-specific cleansing pipeline before tracing
    if preset == "silhouette":
        preprocessed = _binary_mask_for_vectorization(img)
    else:
        preprocessed = _preprocess_for_vectorization(img, num_colors=cfg["colors"], bg_color=bg_color)

    # vtracer requires both an input image path AND an output SVG path
    fd_in, in_path = tempfile.mkstemp(suffix=".png")
    fd_out, out_path = tempfile.mkstemp(suffix=".svg")
    try:
        os.close(fd_in)
        os.close(fd_out)
        preprocessed.save(in_path, "PNG")
        params = dict(
            mode="spline",
            max_iterations=10,
            path_precision=3,
        )
        params.update(cfg["vtracer"])
        params.update(CRISP_TRACE_PARAMS)
        vtracer.convert_image_to_svg_py(in_path, out_path, **params)
        with open(out_path, "r", encoding="utf-8") as f:
            svg_str = f.read()
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass
    # --- Post-process: prune micro-artifacts, purge enclosed bg color, suppress black slivers & depth-sort ---
    svg_str = _prune_and_sort_svg(svg_str, bg_color=bg_color)

    return {"success": True, "svg": svg_str}


def vectorize_advanced(data_url, k_colors=6, detail="balanced", snap_palette=None):
    """Advanced vectorization pipeline with hard-snapped color quantization and
    tunable VTracer spline detail profiles.
    
    A. Hard-Snapped Color Quantization:
       - If snap_palette is provided and non-empty:
         Bypasses K-Means clustering entirely. Converts snap_palette hex strings
         to RGB and forces every non-transparent pixel to the exact nearest brand color.
       - If snap_palette is empty:
         Runs K-Means clustering with n_clusters = k_colors to force the exact requested layers.
         
    B. Tunable VTracer Detail Profiles:
       - 'smooth': corner_threshold=60, filter_speckle=10, length_threshold=5.0
       - 'balanced' (default): corner_threshold=40, filter_speckle=4, length_threshold=3.5
       - 'sharp' / 'typographic': corner_threshold=20, filter_speckle=2, length_threshold=2.5, splice_threshold=30
       - 'ultra' / 'detailed': corner_threshold=10, filter_speckle=1, length_threshold=1.5
    """
    import vtracer
    import numpy as np
    from PIL import Image as PILImage, ImageFilter
    import scipy.cluster.vq as vq
    import warnings
    import tempfile, os

    img = _decode_image(data_url).convert("RGBA")
    arr = np.array(img)
    alpha = arr[..., 3]

    # Preserve alpha if already transparent (e.g. from canvas cutout)
    if (alpha < 128).mean() > 0.05:
        binary_alpha = np.where(alpha > 128, 255, 0).astype(np.uint8)
        raw_rgb = arr[..., :3].copy()
    else:
        try:
            from rembg import remove
            cutout = remove(img, session=session()).convert("RGBA")
            c_arr = np.array(cutout)
            binary_alpha = np.where(c_arr[..., 3] > 140, 255, 0).astype(np.uint8)
            raw_rgb = c_arr[..., :3].copy()
        except Exception:
            binary_alpha = np.full(arr.shape[:2], 255, dtype=np.uint8)
            raw_rgb = arr[..., :3].copy()

    bg_color = _sample_border_color(img)
    if bg_color is not None:
        dist_bg = np.sqrt(np.sum((raw_rgb.astype(np.float32) - np.array(bg_color, dtype=np.float32)) ** 2, axis=2))
        binary_alpha[dist_bg < 18] = 0

    clean_rgb = PILImage.fromarray(raw_rgb, mode="RGB")
    smoothed = clean_rgb.filter(ImageFilter.MedianFilter(size=3))
    smoothed_np = np.array(smoothed)
    mask = binary_alpha > 0
    opaque_pixels = smoothed_np[mask].astype(np.float32)

    # 1. Color Quantization
    valid_palette = []
    if snap_palette and isinstance(snap_palette, list):
        for h in snap_palette:
            if isinstance(h, str):
                hc = h.strip().lstrip("#")
                if len(hc) == 3:
                    hc = "".join(c * 2 for c in hc)
                if len(hc) == 6:
                    try:
                        valid_palette.append([int(hc[0:2], 16), int(hc[2:4], 16), int(hc[4:6], 16)])
                    except ValueError:
                        pass

    if len(opaque_pixels) > 0:
        if len(valid_palette) > 0:
            # Hard-snapped palette: bypass K-Means entirely
            palette_arr = np.array(valid_palette, dtype=np.float32)
            # Euclidean distance to palette colors: (N, 1, 3) - (1, P, 3)
            diff = opaque_pixels[:, None, :] - palette_arr[None, :, :]
            dists = np.sum(diff ** 2, axis=2)
            nearest_idx = np.argmin(dists, axis=1)
            quantized_opaque = palette_arr[nearest_idx].astype(np.uint8)
            num_colors = max(2, len(valid_palette))
        else:
            # K-Means clustering with n_clusters = k_colors
            k = max(2, min(32, int(k_colors or 6)))
            unique_pixels = np.unique(opaque_pixels, axis=0)
            actual_k = max(1, min(k, len(unique_pixels)))

            if len(opaque_pixels) > 30000:
                sample_idx = np.random.choice(len(opaque_pixels), 30000, replace=False)
                sample = opaque_pixels[sample_idx]
            else:
                sample = opaque_pixels

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                centroids, _ = vq.kmeans2(sample, actual_k, minit="points", iter=15)
                labels, _ = vq.vq(opaque_pixels, centroids)

            # Perceptual saturation weighting
            max_c = np.max(opaque_pixels, axis=1)
            min_c = np.min(opaque_pixels, axis=1)
            sat = np.where(max_c > 0, (max_c - min_c) / np.maximum(max_c, 1e-5), 0.0)
            val = max_c / 255.0
            w = ((sat + 0.05) ** 2) * (val + 0.05)

            for ki in range(actual_k):
                m = (labels == ki)
                if m.any():
                    w_sum = np.sum(w[m])
                    centroids[ki] = np.sum(opaque_pixels[m] * w[m, None], axis=0) / w_sum if w_sum > 0 else np.mean(opaque_pixels[m], axis=0)

            quantized_opaque = centroids[labels].clip(0, 255).astype(np.uint8)
            num_colors = actual_k

        out_rgb = smoothed_np.copy()
        out_rgb[mask] = quantized_opaque
        quantized_rgb = PILImage.fromarray(out_rgb, mode="RGB")
    else:
        quantized_rgb = smoothed
        num_colors = 2

    a_clean = PILImage.fromarray(binary_alpha, mode="L")
    r_q, g_q, b_q = quantized_rgb.split()
    preprocessed = PILImage.merge("RGBA", (r_q, g_q, b_q, a_clean))

    # 2. Detail profile mapping
    d_str = str(detail or "balanced").strip().lower()
    if "smooth" in d_str:
        detail_params = dict(
            corner_threshold=60,
            filter_speckle=10,
            length_threshold=5.0,
            splice_threshold=45
        )
    elif "sharp" in d_str or "typo" in d_str:
        detail_params = dict(
            corner_threshold=20,
            filter_speckle=2,
            length_threshold=2.5,
            splice_threshold=30
        )
    elif "ultra" in d_str or "art" in d_str:
        detail_params = dict(
            corner_threshold=10,
            filter_speckle=1,
            length_threshold=1.5,
            splice_threshold=35
        )
    else:  # Balanced (Default)
        detail_params = dict(
            corner_threshold=40,
            filter_speckle=4,
            length_threshold=3.5,
            splice_threshold=45
        )

    # 3. VTracer conversion
    fd_in, in_path = tempfile.mkstemp(suffix=".png")
    fd_out, out_path = tempfile.mkstemp(suffix=".svg")
    try:
        os.close(fd_in)
        os.close(fd_out)
        preprocessed.save(in_path, "PNG")
        params = dict(
            mode="spline",
            max_iterations=10,
            path_precision=3,
            colormode="color",
            hierarchical="stacked",
            color_precision=max(6, min(10, int(num_colors))),
            layer_difference=16,
        )
        params.update(detail_params)
        vtracer.convert_image_to_svg_py(in_path, out_path, **params)
        with open(out_path, "r", encoding="utf-8") as f:
            svg_str = f.read()
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    svg_str = _prune_and_sort_svg(svg_str, bg_color=bg_color)
    return {"success": True, "svg": svg_str}


_SVG_NS = "http://www.w3.org/2000/svg"
_PATH_TOKEN = None


def _svg_path_bbox(d_attr):
    """True bounding box (x, y, w, h) of an SVG path 'd' string.

    Walks real path commands (M/L/H/V/C/S/Q/T/A/Z, absolute and relative) so
    that relative coordinates and single-axis commands are handled correctly.
    Curve control points are included (conservative hull).
    """
    import re
    global _PATH_TOKEN
    if _PATH_TOKEN is None:
        _PATH_TOKEN = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")
    arity = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}

    tokens = _PATH_TOKEN.findall(d_attr or "")
    xs, ys = [], []
    cx = cy = sx = sy = 0.0
    cmd, args, i = None, [], 0

    def emit(x, y):
        xs.append(x)
        ys.append(y)

    while i < len(tokens):
        letter, num = tokens[i]
        i += 1
        if letter:
            cmd = letter
            if cmd in "Zz":
                cx, cy = sx, sy
                cmd = None
            args = []
            continue
        if cmd is None:
            continue
        args.append(float(num))
        up = cmd.upper()
        if len(args) < arity[up]:
            continue
        rel = cmd.islower()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        if up == "M":
            cx, cy = ox + args[0], oy + args[1]
            sx, sy = cx, cy
            emit(cx, cy)
            cmd = "l" if rel else "L"  # implicit lineto after moveto
        elif up == "L" or up == "T":
            cx, cy = ox + args[0], oy + args[1]
            emit(cx, cy)
        elif up == "H":
            cx = (cx if rel else 0.0) + args[0]
            emit(cx, cy)
        elif up == "V":
            cy = (cy if rel else 0.0) + args[0]
            emit(cx, cy)
        elif up == "C":
            emit(ox + args[0], oy + args[1])
            emit(ox + args[2], oy + args[3])
            cx, cy = ox + args[4], oy + args[5]
            emit(cx, cy)
        elif up in ("S", "Q"):
            emit(ox + args[0], oy + args[1])
            cx, cy = ox + args[2], oy + args[3]
            emit(cx, cy)
        elif up == "A":
            cx, cy = ox + args[5], oy + args[6]
            emit(cx, cy)
        args = []

    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def _prune_and_sort_svg(svg_str, min_area=25, min_thickness=2.0, bg_color=None):
    """Post-process vtracer output.

    1. Prune micro-artifacts: paths whose bounding-box area < ``min_area`` px²
       and hairline strips (bbox thinner than ``min_thickness`` px on either
       axis) such as 1-px crop-edge aliasing lines.
    2. Purge enclosed background paths: discard any path whose fill matches
       ``bg_color`` (Euclidean RGB distance < 18) so negative space inside
       geometry (like the cream hexagon interior in ZKV designs) stays 100% transparent.
    3. Black sliver suppression: drop paths with fill #000000 or #010101 having area < 0.8%
       of the total bounding box area (removes crop-edge AA flecks).
    4. Depth-sort the survivors by bounding-box area, descending, so large
       background / extruded-shadow shapes sit at the bottom of the stack and
       small detail shapes (teeth, highlights, eyes) end up on top.
    """
    import xml.etree.ElementTree as ET
    import re

    ET.register_namespace("", _SVG_NS)
    root = ET.fromstring(svg_str)

    def is_path(el):
        return isinstance(el.tag, str) and el.tag.split("}")[-1] == "path"

    def parse_path_color(el):
        f = el.get("fill", "")
        if not f:
            style = el.get("style", "")
            m = re.search(r"fill\s*:\s*([^;]+)", style)
            if m:
                f = m.group(1).strip()
        if not f or f.lower() == "none":
            return None
        f = f.strip()
        if f.startswith("#"):
            if len(f) == 7:
                try:
                    return (int(f[1:3], 16), int(f[3:5], 16), int(f[5:7], 16))
                except ValueError:
                    return None
            elif len(f) == 4:
                try:
                    return (int(f[1] * 2, 16), int(f[2] * 2, 16), int(f[3] * 2, 16))
                except ValueError:
                    return None
        elif f.startswith("rgb"):
            m = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", f)
            if m:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return None

    # Collect every <path> together with its parent
    entries = []
    for parent in root.iter():
        for child in list(parent):
            if is_path(child):
                entries.append((parent, child))
    if not entries:
        return svg_str

    candidates = []
    for parent, p in entries:
        d = p.get("d", "")
        if not d:
            continue
        bx, by, w, h = _svg_path_bbox(d)
        area = w * h
        if area < min_area or min(w, h) < min_thickness:
            continue

        clr = parse_path_color(p)

        # 2. Purge enclosed background paths matching sampled border color
        if bg_color is not None and clr is not None:
            dist = ((clr[0] - bg_color[0]) ** 2 + (clr[1] - bg_color[1]) ** 2 + (clr[2] - bg_color[2]) ** 2) ** 0.5
            if dist < 18.0:
                continue

        # Extract translation if present
        trans = p.get("transform", "")
        tx, ty = 0.0, 0.0
        if trans:
            m = re.search(r"translate\(\s*([-+]?\d*\.?\d+)(?:[,\s]+([-+]?\d*\.?\d+))?\s*\)", trans)
            if m:
                tx = float(m.group(1))
                ty = float(m.group(2)) if m.group(2) else 0.0

        candidates.append({
            "path": p,
            "x": bx + tx,
            "y": by + ty,
            "w": w,
            "h": h,
            "area": area,
            "clr": clr
        })

    for parent, p in entries:
        parent.remove(p)

    if not candidates:
        return ET.tostring(root, encoding="unicode")

    # Union bounding box across all candidates
    min_x = min(c["x"] for c in candidates)
    min_y = min(c["y"] for c in candidates)
    max_x = max(c["x"] + c["w"] for c in candidates)
    max_y = max(c["y"] + c["h"] for c in candidates)
    total_bbox_area = max(1.0, (max_x - min_x) * (max_y - min_y))

    # 3. Black sliver suppression (< 0.8% of total bounds area) & scoring
    scored = []
    for c in candidates:
        clr = c["clr"]
        area = c["area"]
        if clr is not None and clr[0] <= 2 and clr[1] <= 2 and clr[2] <= 2:
            if area < (0.008 * total_bbox_area):
                continue
        scored.append((area, c["path"]))

    if not scored:
        return ET.tostring(root, encoding="unicode")

    # 4. Depth sort: largest first (bottom of z-order), smallest last (top)
    scored.sort(key=lambda t: -t[0])
    for _, p in scored:
        root.append(p)

    return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
#  /api/extract_palette  –  Dominant Brand Palette Extractor
# ---------------------------------------------------------------------------

def extract_palette(data_url):
    """Extract 6-8 dominant brand colors sorted by visual weight and saturation."""
    import numpy as np
    import scipy.cluster.vq as vq
    import warnings

    img = _decode_image(data_url)
    arr = np.array(img)
    if arr.ndim != 3 or arr.shape[0] == 0 or arr.shape[1] == 0:
        return {"success": False, "palette": []}

    mask = arr[..., 3] > 40 if arr.shape[2] == 4 else np.ones(arr.shape[:2], bool)
    pixels = arr[..., :3][mask].astype(np.float32)

    if len(pixels) == 0:
        return {"success": True, "palette": ["#000000"]}

    if len(pixels) > 30000:
        idx = np.random.choice(len(pixels), 30000, replace=False)
        sample = pixels[idx]
    else:
        sample = pixels

    unique_pixels = np.unique(sample, axis=0)
    actual_k = max(1, min(8, len(unique_pixels)))

    if actual_k == 1:
        c = sample.mean(axis=0).astype(int)
        return {"success": True, "palette": [f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"]}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        centroids, _ = vq.kmeans2(sample, actual_k, minit="points", iter=15)
        labels, _ = vq.vq(sample, centroids)

    # For each cluster, compute saturation-weighted centroid and visual score
    clusters = []
    max_c = np.max(sample, axis=1)
    min_c = np.min(sample, axis=1)
    sat = np.where(max_c > 0, (max_c - min_c) / np.maximum(max_c, 1e-5), 0.0)
    val = max_c / 255.0
    w = ((sat + 0.05) ** 2) * (val + 0.05)

    for i in range(actual_k):
        m = (labels == i)
        cnt = int(np.sum(m))
        if cnt == 0:
            continue
        c = np.sum(sample[m] * w[m, None], axis=0) / np.sum(w[m])
        r, g, b = float(c[0]), float(c[1]), float(c[2])
        mx = max(r, g, b)
        mn = min(r, g, b)
        s = (mx - mn) / mx if mx > 0 else 0.0
        v = mx / 255.0
        score = (cnt ** 0.5) * (s + 0.2) * (v + 0.2)
        clusters.append({"rgb": (r, g, b), "score": score, "count": cnt})

    # Sort by visual weight & saturation
    clusters.sort(key=lambda x: -x["score"])

    # Deduplicate clusters that are too close in RGB space (Euclidean distance < 25)
    dedup = []
    for cl in clusters:
        r1, g1, b1 = cl["rgb"]
        if any((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2 < 25 ** 2 for r2, g2, b2 in [d["rgb"] for d in dedup]):
            continue
        dedup.append(cl)

    palette = [f"#{int(round(c['rgb'][0])):02X}{int(round(c['rgb'][1])):02X}{int(round(c['rgb'][2])):02X}" for c in dedup[:8]]
    return {"success": True, "palette": palette}


# ---------------------------------------------------------------------------
#  /api/slice_color  –  Isolate Pixels Matching Swatch (ΔE < 25)
# ---------------------------------------------------------------------------

def slice_color(data_url, target_hex, tolerance=25):
    """Isolate pixels matching target_hex into a dedicated transparent RGBA cutout layer."""
    import numpy as np
    from PIL import Image as PILImage
    import skimage.color

    img = _decode_image(data_url)
    arr = np.array(img)
    if arr.ndim != 3 or arr.shape[0] == 0 or arr.shape[1] == 0:
        return {"success": False, "error": "Invalid image"}

    hex_clean = target_hex.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        return {"success": False, "error": f"Invalid hex color: {target_hex}"}
    try:
        tr = int(hex_clean[0:2], 16)
        tg = int(hex_clean[2:4], 16)
        tb = int(hex_clean[4:6], 16)
    except ValueError:
        return {"success": False, "error": f"Invalid hex color: {target_hex}"}

    rgb = arr[..., :3].astype(np.float32) / 255.0
    alpha = arr[..., 3] if arr.shape[2] == 4 else np.full(arr.shape[:2], 255, dtype=np.uint8)

    t_rgb = np.array([[[tr, tg, tb]]], dtype=np.float32) / 255.0
    t_lab = skimage.color.rgb2lab(t_rgb)[0, 0]

    rgb_lab = skimage.color.rgb2lab(rgb)
    de = skimage.color.deltaE_cie76(rgb_lab, t_lab)

    mask = (de <= float(tolerance)) & (alpha > 40)
    matching_count = int(np.sum(mask))
    if matching_count == 0:
        return {"success": False, "error": "No matching pixels found"}

    ys, xs = np.where(mask)
    x0, x1 = int(xs.min()), int(xs.max() + 1)
    y0, y1 = int(ys.min()), int(ys.max() + 1)

    piece = np.zeros_like(arr)
    piece[mask] = arr[mask]
    crop = PILImage.fromarray(piece[y0:y1, x0:x1], "RGBA")

    return {
        "success": True,
        "png": png_url(crop),
        "x": x0,
        "y": y0,
        "w": x1 - x0,
        "h": y1 - y0,
        "count": matching_count,
        "color": f"#{tr:02X}{tg:02X}{tb:02X}"
    }


# ---------------------------------------------------------------------------
#  /api/ocr  –  Optical character recognition & Font Detective (pytesseract)
# ---------------------------------------------------------------------------

def ocr(data_url):
    """Extract text with preprocessing, Otsu foreground color sampling, and typography classification."""
    import numpy as np
    import pytesseract
    from PIL import ImageEnhance, ImageOps
    from PIL import Image as PILImage
    import scipy.ndimage as ndi

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
        return {
            "success": False,
            "text": "",
            "fontSize": 72,
            "fill": "#000000",
            "detectedFont": "Impact",
            "fontFamily": "Impact"
        }

    fontSize = max(12, int(best_h * 0.85))

    # Sample dominant text colour from the first line's bounding region using Otsu mask
    first_ld = lines[sorted(lines.keys())[0]]
    x1c = max(0, first_ld["x"])
    y1c = max(0, first_ld["y"])
    x2c = min(arr.shape[1], first_ld["x2"])
    y2c = min(arr.shape[0], first_ld["y2"])
    region = arr[y1c:y2c, x1c:x2c]

    fill = "#000000"
    detected_font = "Montserrat"
    font_family = "Montserrat, Arial, sans-serif"

    if region.size > 0 and region.shape[0] >= 2 and region.shape[1] >= 2:
        gray = np.array(PILImage.fromarray(region).convert("L"))
        t = _otsu_threshold(gray)
        border_vals = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
        bg_is_light = np.median(border_vals) > t
        fg_mask = (gray <= t) if bg_is_light else (gray > t)

        if fg_mask.any():
            fg_pixels = region[fg_mask]
            # Sample median foreground RGB strictly within the Otsu text mask
            med_rgb = np.median(fg_pixels, axis=0).astype(int)
            fill = f"#{int(med_rgb[0]):02X}{int(med_rgb[1]):02X}{int(med_rgb[2]):02X}"

            # Typography Classification
            reg_h, reg_w = region.shape[:2]
            clean_chars = [c for c in full_text if c.isalnum()]
            n_chars = max(1, len(clean_chars))
            char_w = max(1.0, reg_w / n_chars)
            aspect_ratio = reg_h / char_w
            density = float(np.mean(fg_mask))

            dist = ndi.distance_transform_edt(fg_mask)
            stroke_radius = float(np.max(dist)) if fg_mask.any() else 1.0
            stroke_weight = (2.0 * stroke_radius) / max(1.0, reg_h)

            dist_vals = dist[fg_mask]
            variance_ratio = float(np.std(dist_vals) / np.mean(dist_vals)) if len(dist_vals) > 0 and np.mean(dist_vals) > 0 else 0.0

            # 1. Condensed Headline (Bebas Neue / Impact)
            if aspect_ratio >= 1.40 or (aspect_ratio >= 1.25 and stroke_weight < 0.16):
                detected_font = "Bebas Neue"
                font_family = "Bebas Neue, Impact, sans-serif"
            # 2. Rounded Retro / Heavy (Cooper Black / Fatface)
            elif density >= 0.44 or stroke_weight >= 0.22:
                detected_font = "Cooper Black"
                font_family = "Cooper Black, Impact, serif"
            # 3. Serif (Georgia)
            elif variance_ratio > 0.65:
                detected_font = "Georgia"
                font_family = "Georgia, serif"
            # 4. Geometric Sans (Montserrat / Arial)
            else:
                detected_font = "Montserrat"
                font_family = "Montserrat, Arial, sans-serif"
        else:
            med_rgb = np.median(region, axis=(0, 1)).astype(int)
            fill = f"#{int(med_rgb[0]):02X}{int(med_rgb[1]):02X}{int(med_rgb[2]):02X}"

    return {
        "success": True,
        "text": full_text,
        "fontSize": fontSize,
        "fill": fill,
        "detectedFont": detected_font,
        "fontFamily": font_family
    }


# ---------------------------------------------------------------------------
#  HTTP handler
# ---------------------------------------------------------------------------

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            self.close_connection = True

    def send_json(self, obj, code=200):
        try:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def do_GET(self):
        try:
            if self.path.split("?")[0] == "/health":
                return self.send_json({"app": APP, "status": "online"})
            super().do_GET()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception as e:
            return self.send_json({"error": f"Bad request: {e}"}, 400)
        try:
            if path in ("/api/cutout", "/api/ai_segment"):
                mode = body.get("mode", "auto")
                tolerance = float(body.get("tolerance", 22.0))
                return self.send_json(dual_engine_cutout(body["image"], mode=mode, tolerance=tolerance))
            if path == "/api/vectorize":
                return self.send_json(vectorize(body["image"], body.get("preset", DEFAULT_PRESET)))
            if path == "/api/vectorize_advanced":
                k_colors = int(body.get("k_colors", 6))
                detail = body.get("detail", "balanced")
                snap_palette = body.get("snap_palette", None)
                return self.send_json(vectorize_advanced(body["image"], k_colors=k_colors, detail=detail, snap_palette=snap_palette))
            if path == "/api/ocr":
                return self.send_json(ocr(body["image"]))
            if path == "/api/extract_palette":
                return self.send_json(extract_palette(body["image"]))
            if path == "/api/slice_color":
                return self.send_json(slice_color(body["image"], body.get("color", "#000000"), body.get("tolerance", 25)))
            if path == "/api/export_psd":
                return self.send_json({"success": True, "message": "PSD export handled"})
            self.send_json({"error": "not found"}, 404)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass
        except Exception as e:
            try:
                self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)
            except Exception:
                pass


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
