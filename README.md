# Miko Studio Slicer

**Miko Studio Slicer** is an offline-first, browser-based graphic workstation that decomposes flat raster graphics, generative AI concepts, and brand artboards into editable, multi-layer production assets. 

Equipped with Bézier vector path extraction, multi-color OCR typography reconstruction, perceptual CIE-Lab color slicing, and an integrated SMPTE broadcast lower-third engine, Miko Studio Slicer bridges the gap between flattened concept art and structured Adobe Photoshop/Illustrator files.

---

## Key Features

- component-Level Vector Decomposition: Automatically trace raster marks into smooth Bézier splines (`.SVG`) using perceptual saturation-weighted K-Means clustering—preserving vibrant brand colors without edge halos or muddy banding.
- Font Detective & Smart OCR: Recognizes text blocks, extracts exact foreground character core colors, and classifies typography styles (Retro Display, Ultra-Condensed, Geometric Sans, Serif) to instantiate live, editable `fabric.IText` objects.
- CIE-Lab Spot Color Separation: Isolate distinct ink passes and spot colors with one click using perceptual color distance (Delta E < 25).
- Multi-Layer PSD Compilation: Exports clean binary `.PSD` files natively in the browser via `ag-psd` with full preservation of layer transparency, coordinates, and typography.
- Broadcast Lower-Third Studio: Rapidly mount extracted marks into title-safe 1080p broadcast badges. Export transparent PNG overlays or standalone animated HTML/CSS browser sources for OBS Studio and wMix.
- Portable / Flash Drive Ready: Zero external cloud dependencies. Can run entirely from a USB thumb drive using embedded Python.

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + C` / `Ctrl + V` | Copy / Paste active layer with visual offset |
| `Ctrl + X` / `Ctrl + D` | Cut / Duplicate layer in place |
| `Ctrl + Z` / `Ctrl + Y` | 40-State Undo / Redo |
| `Delete` / `Backspace` | Delete active selection |
| `Arrow Keys` | Nudge 1px (`Shift + Arrow` for 10px) |
| `Spacebar + Drag` | Pan canvas viewport |
| `Alt + Mouse Wheel` | Smooth zoom centered on cursor (0.2x to 10x) |
| `I` | Native Eyedropper tool |

---

## Installation & Quick Start

### Standard Host Installation (Windows 10/11)
1. Clone the repository:
   ```bash
   git clone https://github.com/phantomsound/mikostudioslicer.git
   cd mikostudioslicer
   ```
2. Run the automated installer:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```
3. Open `http://localhost:8088` in your browser.

### Portable USB Flash Drive Execution
1. Copy the repository contents onto your USB drive (e.g., `E:\MikostudioSlicer\`).
2. Download the official **Windows embeddable package (64-bit)** from [python.org](https://www.python.org/downloads/windows/) and extract it into `python_portable\`.
3. Copy installed site-packages into `python_portable\Lib\site-packages\`.
4. Double-click `run_portable.bat`. The server will dynamically detect an open port (8088–8138) and launch your browser automatically.

---

## Architecture

- **Frontend:** Single-page application powered by Fabric.js, Tailwind CSS, Lucide icons, and `ag-psd`.
- **Backend:** Python micro-service utilizing `rembg` (u2net) for salient object isolation, `vtracer` for spline conversion, and `pytesseract` for optical character recognition.

---

## License

Distributed under the [MIT License](LICENSE).
