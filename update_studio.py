import os
import sys
import shutil
from PIL import Image, ImageDraw

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = r"C:\Program Files (x86)\Miko Studio Slicer"

print("[*] Generating custom Miko Studio Slicer multi-resolution icon (.ico)...")
sizes = [(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)]
images = []
for s in sizes:
    w, h = s
    img = Image.new("RGBA", s, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rad = max(2, int(w * 0.22))
    d.rounded_rectangle([0, 0, w-1, h-1], radius=rad, fill=(18, 20, 26, 255), outline=(245, 158, 11, 230), width=max(1, int(w*0.04)))
    if w >= 32:
        d.polygon([(w*0.2, h*0.78), (w*0.2, h*0.24), (w*0.35, h*0.24), (w*0.35, h*0.78)], fill=(245, 158, 11, 255))
        d.polygon([(w*0.65, h*0.78), (w*0.65, h*0.24), (w*0.8, h*0.24), (w*0.8, h*0.78)], fill=(245, 158, 11, 255))
        d.polygon([(w*0.35, h*0.24), (w*0.5, h*0.56), (w*0.65, h*0.24), (w*0.5, h*0.42)], fill=(251, 191, 36, 255))
        d.line([(w*0.12, h*0.72), (w*0.88, h*0.28)], fill=(6, 182, 212, 255), width=max(1, int(w*0.06)))
    else:
        d.rectangle([w*0.25, h*0.25, w*0.75, h*0.75], fill=(245, 158, 11, 255))
    images.append(img)

ico_path = os.path.join(APP_DIR, "icon.ico")
images[0].save(ico_path, format="ICO", sizes=[(im.width, im.height) for im in images])
print("    [+] icon.ico created successfully.")

print("[*] Writing sanitized install.ps1 (semicolon-terminated, no taskbar logic)...")
install_ps1_content = """Add-Type -AssemblyName System.Windows.Forms, System.Drawing;
[System.Windows.Forms.Application]::EnableVisualStyles();

$f = New-Object Windows.Forms.Form;
$f.Text = "Miko Studio Slicer Setup";
$f.Size = New-Object Drawing.Size(520, 410);
$f.StartPosition = "CenterScreen";
$f.FormBorderStyle = "FixedDialog";
$f.MaximizeBox = $false;
$f.BackColor = [Drawing.Color]::FromArgb(15, 23, 42);
$f.ForeColor = [Drawing.Color]::White;

$lbl = New-Object Windows.Forms.Label;
$lbl.Text = "Miko Studio Slicer Setup";
$lbl.Font = New-Object Drawing.Font("Segoe UI", 13, [Drawing.FontStyle]::Bold);
$lbl.Location = New-Object Drawing.Point(20, 15);
$lbl.Size = New-Object Drawing.Size(460, 28);
$lbl.ForeColor = [Drawing.Color]::FromArgb(245, 158, 11);
$f.Controls.Add($lbl);

$lp = New-Object Windows.Forms.Label;
$lp.Text = "Install Folder:";
$lp.Location = New-Object Drawing.Point(20, 52);
$lp.Size = New-Object Drawing.Size(460, 18);
$f.Controls.Add($lp);

$tb = New-Object Windows.Forms.TextBox;
$tb.Text = "C:\\\\Program Files (x86)\\\\Miko Studio Slicer";
$tb.Location = New-Object Drawing.Point(20, 72);
$tb.Size = New-Object Drawing.Size(370, 24);
$tb.BackColor = [Drawing.Color]::FromArgb(30, 41, 59);
$tb.ForeColor = [Drawing.Color]::White;
$f.Controls.Add($tb);

$btnB = New-Object Windows.Forms.Button;
$btnB.Text = "Browse...";
$btnB.Location = New-Object Drawing.Point(400, 70);
$btnB.Size = New-Object Drawing.Size(80, 28);
$btnB.BackColor = [Drawing.Color]::FromArgb(51, 65, 85);
$btnB.ForeColor = [Drawing.Color]::White;
$btnB.FlatStyle = "Flat";
$btnB.Add_Click({
    $d = New-Object Windows.Forms.FolderBrowserDialog;
    $d.SelectedPath = $tb.Text;
    if ($d.ShowDialog() -eq [Windows.Forms.DialogResult]::OK) { $tb.Text = $d.SelectedPath; };
});
$f.Controls.Add($btnB);

$grp = New-Object Windows.Forms.GroupBox;
$grp.Text = "Installation Options";
$grp.Location = New-Object Drawing.Point(20, 115);
$grp.Size = New-Object Drawing.Size(460, 150);
$grp.ForeColor = [Drawing.Color]::FromArgb(203, 213, 225);
$f.Controls.Add($grp);

$c1 = New-Object Windows.Forms.CheckBox;
$c1.Text = "Install local background service (Auto-detects open port 8088+)";
$c1.Checked = $true;
$c1.Location = New-Object Drawing.Point(15, 28);
$c1.Size = New-Object Drawing.Size(430, 24);
$grp.Controls.Add($c1);

$c2 = New-Object Windows.Forms.CheckBox;
$c2.Text = "Start local service automatically when Windows boots";
$c2.Checked = $true;
$c2.Location = New-Object Drawing.Point(15, 62);
$c2.Size = New-Object Drawing.Size(430, 24);
$grp.Controls.Add($c2);

$c3 = New-Object Windows.Forms.CheckBox;
$c3.Text = "Create Desktop Shortcut with custom Miko Studio Slicer icon";
$c3.Checked = $true;
$c3.Location = New-Object Drawing.Point(15, 96);
$c3.Size = New-Object Drawing.Size(430, 24);
$grp.Controls.Add($c3);

$st = New-Object Windows.Forms.Label;
$st.Location = New-Object Drawing.Point(20, 310);
$st.Size = New-Object Drawing.Size(290, 25);
$st.ForeColor = [Drawing.Color]::FromArgb(148, 163, 184);
$f.Controls.Add($st);

$btnI = New-Object Windows.Forms.Button;
$btnI.Text = "Install Now";
$btnI.Font = New-Object Drawing.Font("Segoe UI", 10, [Drawing.FontStyle]::Bold);
$btnI.Location = New-Object Drawing.Point(320, 300);
$btnI.Size = New-Object Drawing.Size(160, 40);
$btnI.BackColor = [Drawing.Color]::FromArgb(245, 158, 11);
$btnI.ForeColor = [Drawing.Color]::FromArgb(15, 23, 42);
$btnI.FlatStyle = "Flat";

$btnI.Add_Click({
    $btnI.Enabled = $false;
    $dst = $tb.Text.Trim();
    $src = $PSScriptRoot;
    try {
        $st.Text = "Copying files..."; $f.Refresh();
        if (-not (Test-Path -LiteralPath $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null; };
        Start-Process "icacls" -ArgumentList "`"$dst`"", "/grant", "Users:(OI)(CI)M", "/T", "/Q" -Wait -NoNewWindow;
        $copyFiles = @("index.html", "requirements.txt", "setup_illustrator.jsx", "slicer_engine.py", "server.py", "uninstall.ps1", "icon.ico", "sample_concept.png");
        foreach ($fn in $copyFiles) {
            $sf = "$src\\$fn";
            if (Test-Path -LiteralPath $sf) { Copy-Item -LiteralPath $sf -Destination $dst -Force; };
        };
        $st.Text = "Configuring Python virtual environment..."; $f.Refresh();
        $py = if (Get-Command "python.exe" -ErrorAction SilentlyContinue) { "python.exe" } elseif (Get-Command "py.exe" -ErrorAction SilentlyContinue) { "py.exe" } else { throw "Python not found in system PATH."; };
        $v = "$dst\\venv";
        if (-not (Test-Path -LiteralPath $v)) { Start-Process $py -ArgumentList "-m", "venv", "`"$v`"" -Wait -NoNewWindow; };
        $pip = "$v\\Scripts\\pip.exe"; $req = "$dst\\requirements.txt";
        if (Test-Path -LiteralPath $pip) { Start-Process $pip -ArgumentList "install", "-r", "`"$req`"" -Wait -NoNewWindow; };
        $pyw = "$v\\Scripts\\pythonw.exe"; if (-not (Test-Path -LiteralPath $pyw)) { $pyw = "pythonw.exe"; };
        $srv = "$dst\\server.py";
        $iconPath = "$dst\\icon.ico";
        $wsh = New-Object -ComObject WScript.Shell;
        if ($c3.Checked) {
            $desk = [Environment]::GetFolderPath("Desktop");
            $sc = $wsh.CreateShortcut("$desk\\Miko Studio Slicer.lnk");
            $sc.TargetPath = $pyw;
            $sc.Arguments = "`"$srv`" --launch";
            $sc.WorkingDirectory = $dst;
            $sc.Description = "Miko Studio Slicer Production Studio";
            if (Test-Path -LiteralPath $iconPath) { $sc.IconLocation = "$iconPath,0"; };
            $sc.Save();
        };
        $sm = [Environment]::GetFolderPath("StartMenu");
        $smd = "$sm\\Programs\\Miko Studio Slicer";
        if (-not (Test-Path -LiteralPath $smd)) { New-Item -ItemType Directory -Path $smd -Force | Out-Null; };
        $scSm = $wsh.CreateShortcut("$smd\\Miko Studio Slicer.lnk");
        $scSm.TargetPath = $pyw;
        $scSm.Arguments = "`"$srv`" --launch";
        $scSm.WorkingDirectory = $dst;
        $scSm.Description = "Miko Studio Slicer Production Studio";
        if (Test-Path -LiteralPath $iconPath) { $scSm.IconLocation = "$iconPath,0"; };
        $scSm.Save();
        if ($c2.Checked) {
            Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "MikoStudioSlicerService" -Value "`"$pyw`" `"$srv`"";
        };
        if ($c1.Checked) {
            Start-Process $pyw -ArgumentList "`"$srv`" --launch" -WorkingDirectory $dst;
        };
        [Windows.Forms.MessageBox]::Show("Miko Studio Slicer installed successfully to:`n$dst", "Setup Complete", [Windows.Forms.MessageBoxButtons]::OK, [Windows.Forms.MessageBoxIcon]::Information);
        $f.Close();
    } catch {
        [Windows.Forms.MessageBox]::Show("Installation failed with error:`n`n$($_.Exception.Message)", "Install Error", [Windows.Forms.MessageBoxButtons]::OK, [Windows.Forms.MessageBoxIcon]::Error);
        $btnI.Enabled = $true; $st.Text = "Installation failed.";
    };
});
$f.Controls.Add($btnI);
$f.ShowDialog() | Out-Null;
"""

with open(os.path.join(APP_DIR, "install.ps1"), "w", encoding="utf-8") as f:
    f.write(install_ps1_content)
print("    [+] install.ps1 written.")

print("[*] Writing Photoshop-grade interactive studio (index.html with Fabric.js)...")
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Miko Studio Slicer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Fabric.js provides the live interactive Photoshop/Illustrator canvas object engine -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/ag-psd/dist/bundle.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
  <style>
    .checker-pattern {
      background-image: linear-gradient(45deg, #1c1d22 25%, transparent 25%),
                        linear-gradient(-45deg, #1c1d22 25%, transparent 25%),
                        linear-gradient(45deg, transparent 75%, #1c1d22 75%),
                        linear-gradient(-45deg, transparent 75%, #1c1d22 75%);
      background-size: 16px 16px;
      background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
      background-color: #141418;
    }
  </style>
</head>
<body class="bg-[#121316] text-slate-100 min-h-screen flex flex-col font-sans antialiased selection:bg-amber-500 selection:text-black">

  <!-- APP HEADER -->
  <header class="border-b border-[#24252f] bg-[#18191f]/90 backdrop-blur px-6 py-3 flex items-center justify-between sticky top-0 z-40">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-black text-lg">
        M
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-sm font-semibold tracking-wide text-slate-100">Miko Studio Slicer</h1>
          <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">Photoshop Layer Studio</span>
        </div>
        <p class="text-xs text-slate-400">Deconstruct Images into Live Editable Text, Vector Blocks & AI Cutouts</p>
      </div>
    </div>

    <!-- WORKSPACE TABS -->
    <div class="flex items-center bg-[#1e2027] border border-[#2b2d37] p-1 rounded-xl text-xs font-medium">
      <button id="tabDeconstruct" class="px-3.5 py-1.5 rounded-lg bg-amber-500/15 text-amber-300 font-semibold transition flex items-center gap-1.5">
        <i data-lucide="scissors" class="w-3.5 h-3.5"></i> 1. Pull & Deconstruct
      </button>
      <button id="tabCanvas" class="px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition flex items-center gap-1.5">
        <i data-lucide="layers" class="w-3.5 h-3.5"></i> 2. Photoshop Canvas
      </button>
      <button id="tabLowerThird" class="px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition flex items-center gap-1.5">
        <i data-lucide="tv" class="w-3.5 h-3.5"></i> 3. Lower Third Studio
      </button>
    </div>

    <!-- ACTIONS -->
    <div class="flex items-center gap-2.5">
      <label class="cursor-pointer bg-[#20222a] hover:bg-[#282a35] text-xs font-medium text-slate-200 px-3.5 py-2 rounded-lg border border-[#2e313d] transition flex items-center gap-1.5">
        <i data-lucide="upload" class="w-3.5 h-3.5 text-indigo-400"></i> Upload Concept
        <input type="file" id="fileInput" accept="image/*" class="hidden">
      </label>
      <button id="btnExportPSD" class="bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold px-4 py-2 rounded-lg shadow-sm transition flex items-center gap-2">
        <i data-lucide="file-output" class="w-4 h-4"></i> Export Layered .PSD
      </button>
    </div>
  </header>

  <!-- MAIN WORKSPACE -->
  <main class="flex-1 flex overflow-hidden">
    <!-- VIEWPORT AREA -->
    <div class="flex-1 flex flex-col p-5 overflow-hidden">
      <!-- Toolbar -->
      <div class="mb-3 flex items-center justify-between bg-[#18191f] border border-[#262833] px-4 py-2 rounded-xl text-xs">
        <div id="toolbarDeconstruct" class="flex items-center gap-3">
          <span class="text-slate-400">Box selection mode:</span>
          <button id="btnModeText" class="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-medium">
            <i data-lucide="type" class="w-3 h-3"></i> Extract as Live Text
          </button>
          <button id="btnModeBlock" class="px-2.5 py-1 rounded text-slate-300 hover:text-white border border-[#2c2f3d] flex items-center gap-1">
            <i data-lucide="square" class="w-3 h-3"></i> Extract as Vector Block
          </button>
          <button id="btnModeCutout" class="px-2.5 py-1 rounded text-slate-300 hover:text-white border border-[#2c2f3d] flex items-center gap-1">
            <i data-lucide="sparkles" class="w-3 h-3 text-emerald-400"></i> Extract as AI Cutout
          </button>
        </div>

        <div id="toolbarCanvas" class="flex items-center gap-3 hidden">
          <span class="text-slate-400">Transform: Click any element to drag, resize, rotate, or re-type live text.</span>
          <button id="btnBringForward" class="px-2 py-1 rounded bg-[#20222a] border border-slate-700 text-slate-300 hover:text-white">Bring Forward</button>
          <button id="btnSendBackward" class="px-2 py-1 rounded bg-[#20222a] border border-slate-700 text-slate-300 hover:text-white">Send Backward</button>
        </div>

        <div id="toolbarLowerThird" class="flex items-center gap-3 hidden">
          <span class="text-slate-400">SMPTE 1920x1080 Broadcast Viewport.</span>
          <button id="btnExport1080pPNG" class="px-3 py-1 rounded bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 flex items-center gap-1">
            <i data-lucide="download" class="w-3 h-3"></i> Download 1080p Broadcast PNG
          </button>
        </div>

        <div id="statusText" class="text-slate-400 font-mono text-[11px]">Ready</div>
      </div>

      <!-- Stage Container -->
      <div class="flex-1 rounded-2xl border border-[#242631] checker-pattern relative overflow-auto flex items-center justify-center p-6" id="stageContainer">
        <!-- 1. Source Extraction Canvas -->
        <canvas id="sourceCanvas" class="shadow-2xl max-w-full max-h-full cursor-crosshair rounded border border-slate-700/40"></canvas>

        <!-- 2. Photoshop Interactive Fabric Canvas -->
        <div id="fabricWrapper" class="hidden shadow-2xl rounded border border-slate-700/60 overflow-hidden">
          <canvas id="fabricCanvas" width="1280" height="720"></canvas>
        </div>

        <!-- 3. Broadcast Lower Third Stage -->
        <div id="lowerThirdStage" class="hidden relative border border-dashed border-indigo-500/40 bg-black/75 shadow-2xl flex items-end p-16" style="width: 1280px; height: 720px;">
          <div class="absolute inset-[10%] border border-cyan-500/30 pointer-events-none flex items-start justify-end p-2 text-[10px] font-mono text-cyan-400">
            TITLE SAFE (80%)
          </div>
          <div id="ltBannerBox" class="relative z-10 flex items-center gap-4 bg-[#0f172a] border border-amber-500/50 p-4 rounded-2xl shadow-2xl min-w-[540px]">
            <div id="ltIconSlot" class="w-20 h-20 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center overflow-hidden shrink-0">
              <i data-lucide="image" class="w-8 h-8 text-amber-400"></i>
            </div>
            <div class="flex-1">
              <div id="ltRoleDisplay" class="text-xs uppercase font-extrabold tracking-wider text-amber-400 mb-0.5">SPEAKER ROLE / TITLE</div>
              <div id="ltNameDisplay" class="text-2xl font-black tracking-tight text-white">SPEAKER NAME HERE</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT: LAYER STACK & PROPERTY INSPECTOR -->
    <div class="w-96 border-l border-[#24252f] bg-[#18191f]/60 backdrop-blur p-5 flex flex-col justify-between overflow-y-auto">
      <div>
        <div class="flex items-center justify-between pb-3 border-b border-[#252733] mb-4">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-300">Photoshop Layers</h2>
          <span id="layerCountBadge" class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">0 Layers</span>
        </div>

        <!-- Dynamic Property Inspector -->
        <div id="inspectorPanel" class="mb-4 bg-[#14151a] p-3.5 rounded-xl border border-[#262834] space-y-3">
          <div class="flex items-center justify-between text-xs font-bold text-amber-400">
            <span id="inspectorTitle">No Object Selected</span>
            <span id="inspectorType" class="text-[10px] text-slate-400 font-mono">Click canvas item</span>
          </div>

          <!-- Text Properties -->
          <div id="textControls" class="space-y-2 hidden">
            <div>
              <label class="text-[11px] text-slate-400">Edit Text Content:</label>
              <input type="text" id="propTextContent" class="w-full bg-[#1c1d24] border border-slate-700 px-2 py-1 rounded text-xs text-white mt-0.5">
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="text-[11px] text-slate-400">Font:</label>
                <select id="propFontFamily" class="w-full bg-[#1c1d24] border border-slate-700 px-2 py-1 rounded text-xs text-white mt-0.5">
                  <option value="Arial">Arial</option>
                  <option value="Impact">Impact (Headline)</option>
                  <option value="Trebuchet MS">Trebuchet MS</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Courier New">Courier New</option>
                </select>
              </div>
              <div>
                <label class="text-[11px] text-slate-400">Size:</label>
                <input type="number" id="propFontSize" min="8" max="250" class="w-full bg-[#1c1d24] border border-slate-700 px-2 py-1 rounded text-xs text-white mt-0.5">
              </div>
            </div>
            <div class="flex items-center gap-2 pt-1">
              <label class="text-[11px] text-slate-400">Color:</label>
              <input type="color" id="propTextColor" class="w-7 h-7 rounded border border-slate-700 cursor-pointer bg-transparent">
            </div>
          </div>

          <!-- Shape / Block Properties -->
          <div id="shapeControls" class="space-y-2 hidden">
            <div class="flex items-center justify-between">
              <label class="text-[11px] text-slate-400">Fill Color:</label>
              <input type="color" id="propShapeFill" class="w-7 h-7 rounded border border-slate-700 cursor-pointer bg-transparent">
            </div>
            <div class="flex items-center justify-between">
              <label class="text-[11px] text-slate-400">Stroke Color:</label>
              <input type="color" id="propShapeStroke" class="w-7 h-7 rounded border border-slate-700 cursor-pointer bg-transparent">
            </div>
            <div>
              <label class="text-[11px] text-slate-400">Border Radius:</label>
              <input type="range" id="propShapeRadius" min="0" max="50" value="0" class="w-full accent-amber-500">
            </div>
          </div>

          <!-- Cutout / Image Properties -->
          <div id="imageControls" class="space-y-2 hidden">
            <button id="btnRunAIDefringe" class="w-full bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs py-1.5 rounded flex items-center justify-center gap-1 font-semibold">
              <i data-lucide="sparkles" class="w-3.5 h-3.5"></i> Run Local AI Neural Cutout
            </button>
          </div>
        </div>

        <!-- Layers List -->
        <div id="layersList" class="space-y-2"></div>
      </div>

      <!-- Footer Buttons -->
      <div class="pt-4 border-t border-[#252733] space-y-2">
        <button id="btnExportSVG" class="w-full bg-[#20222a] hover:bg-[#282a35] text-slate-200 text-xs font-semibold py-2.5 rounded-lg border border-[#2e313d] transition flex items-center justify-center gap-2">
          <i data-lucide="bezier" class="w-4 h-4 text-indigo-400"></i> Export Scalable Vector (.SVG)
        </button>
      </div>
    </div>
  </main>

  <script>
    lucide.createIcons();

    // 1. Source Image Setup
    const sCanvas = document.getElementById('sourceCanvas');
    const sCtx = sCanvas.getContext('2d');
    let sourceImg = new Image();
    let isDrawing = false;
    let startX = 0, startY = 0;
    let extractMode = 'text'; // 'text', 'block', 'cutout'

    // 2. Fabric.js Interactive Canvas
    const fCanvas = new fabric.Canvas('fabricCanvas', {
      backgroundColor: '#12141A',
      preserveObjectStacking: true
    });

    sourceImg.onload = () => {
      sCanvas.width = sourceImg.width;
      sCanvas.height = sourceImg.height;
      redrawSource();
    };
    sourceImg.src = "sample_concept.png";

    document.getElementById('fileInput').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (evt) => {
        sourceImg = new Image();
        sourceImg.onload = () => {
          sCanvas.width = sourceImg.width;
          sCanvas.height = sourceImg.height;
          redrawSource();
          document.getElementById('statusText').innerText = `Loaded: ${file.name}`;
        };
        sourceImg.src = evt.target.result;
      };
      reader.readAsDataURL(file);
    });

    // Box extraction on source canvas
    sCanvas.addEventListener('mousedown', (e) => {
      const rect = sCanvas.getBoundingClientRect();
      const sx = sCanvas.width / rect.width;
      const sy = sCanvas.height / rect.height;
      startX = (e.clientX - rect.left) * sx;
      startY = (e.clientY - rect.top) * sy;
      isDrawing = true;
    });

    sCanvas.addEventListener('mousemove', (e) => {
      if (!isDrawing) return;
      const rect = sCanvas.getBoundingClientRect();
      const sx = sCanvas.width / rect.width;
      const sy = sCanvas.height / rect.height;
      const curX = (e.clientX - rect.left) * sx;
      const curY = (e.clientY - rect.top) * sy;

      redrawSource();
      sCtx.strokeStyle = '#f59e0b';
      sCtx.lineWidth = 2;
      sCtx.strokeRect(startX, startY, curX - startX, curY - startY);
    });

    sCanvas.addEventListener('mouseup', (e) => {
      if (!isDrawing) return;
      isDrawing = false;
      const rect = sCanvas.getBoundingClientRect();
      const sx = sCanvas.width / rect.width;
      const sy = sCanvas.height / rect.height;
      const endX = (e.clientX - rect.left) * sx;
      const endY = (e.clientY - rect.top) * sy;

      const x = Math.min(startX, endX);
      const y = Math.min(startY, endY);
      const w = Math.abs(endX - startX);
      const h = Math.abs(endY - startY);

      if (w > 15 && h > 15) {
        deconstructRegion(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
      }
      redrawSource();
    });

    function redrawSource() {
      sCtx.clearRect(0, 0, sCanvas.width, sCanvas.height);
      sCtx.drawImage(sourceImg, 0, 0);
    }

    // Extraction Engine: Converts region into Live Text, Vector Block, or Cutout
    function deconstructRegion(x, y, w, h) {
      // Sample center pixel color for default text/block color
      const centerPixel = sCtx.getImageData(x + w/2, y + h/2, 1, 1).data;
      const sampledHex = "#" + ((1 << 24) + (centerPixel[0] << 16) + (centerPixel[1] << 8) + centerPixel[2]).toString(16).slice(1);

      if (extractMode === 'text') {
        const textVal = prompt("Enter text for this live layer (or keep default):", "UPSTAIRS") || "SAMPLE TEXT";
        const textObj = new fabric.IText(textVal, {
          left: 100 + (fCanvas.getObjects().length * 20),
          top: 100 + (fCanvas.getObjects().length * 20),
          fontFamily: 'Impact',
          fontSize: Math.max(18, Math.round(h * 0.7)),
          fill: sampledHex,
          name: `Text: ${textVal}`
        });
        fCanvas.add(textObj);
        fCanvas.setActiveObject(textObj);
      } else if (extractMode === 'block') {
        const rectObj = new fabric.Rect({
          left: 100 + (fCanvas.getObjects().length * 20),
          top: 100 + (fCanvas.getObjects().length * 20),
          width: w,
          height: h,
          fill: sampledHex,
          stroke: '#F59E0B',
          strokeWidth: 2,
          rx: 8,
          ry: 8,
          name: `Block: ${w}x${h}`
        });
        fCanvas.add(rectObj);
        fCanvas.setActiveObject(rectObj);
      } else if (extractMode === 'cutout') {
        const tempC = document.createElement('canvas');
        tempC.width = w;
        tempC.height = h;
        tempC.getContext('2d').drawImage(sourceImg, x, y, w, h, 0, 0, w, h);

        fabric.Image.fromURL(tempC.toDataURL(), (imgObj) => {
          imgObj.set({
            left: 100 + (fCanvas.getObjects().length * 20),
            top: 100 + (fCanvas.getObjects().length * 20),
            name: `Cutout: ${w}x${h}`
          });
          fCanvas.add(imgObj);
          fCanvas.setActiveObject(imgObj);
        });
      }

      switchTab('canvas');
      updateLayersUI();
      document.getElementById('statusText').innerText = `Extracted as ${extractMode.toUpperCase()}`;
    }

    // Tool Mode Toggles
    const modes = [
      { id: 'btnModeText', mode: 'text' },
      { id: 'btnModeBlock', mode: 'block' },
      { id: 'btnModeCutout', mode: 'cutout' }
    ];

    modes.forEach(m => {
      document.getElementById(m.id).addEventListener('click', () => {
        extractMode = m.mode;
        modes.forEach(o => {
          document.getElementById(o.id).className = (o.mode === extractMode)
            ? "px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-medium"
            : "px-2.5 py-1 rounded text-slate-300 hover:text-white border border-[#2c2f3d] flex items-center gap-1";
        });
      });
    });

    // Tab Switching
    document.getElementById('tabDeconstruct').addEventListener('click', () => switchTab('deconstruct'));
    document.getElementById('tabCanvas').addEventListener('click', () => switchTab('canvas'));
    document.getElementById('tabLowerThird').addEventListener('click', () => switchTab('lowerthird'));

    function switchTab(t) {
      ['tabDeconstruct', 'tabCanvas', 'tabLowerThird'].forEach(id => {
        document.getElementById(id).className = "px-3.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 transition flex items-center gap-1.5";
      });

      document.getElementById('toolbarDeconstruct').classList.add('hidden');
      document.getElementById('toolbarCanvas').classList.add('hidden');
      document.getElementById('toolbarLowerThird').classList.add('hidden');

      sCanvas.classList.add('hidden');
      document.getElementById('fabricWrapper').classList.add('hidden');
      document.getElementById('lowerThirdStage').classList.add('hidden');

      if (t === 'deconstruct') {
        document.getElementById('tabDeconstruct').className = "px-3.5 py-1.5 rounded-lg bg-amber-500/15 text-amber-300 font-semibold transition flex items-center gap-1.5";
        document.getElementById('toolbarDeconstruct').classList.remove('hidden');
        sCanvas.classList.remove('hidden');
      } else if (t === 'canvas') {
        document.getElementById('tabCanvas').className = "px-3.5 py-1.5 rounded-lg bg-amber-500/15 text-amber-300 font-semibold transition flex items-center gap-1.5";
        document.getElementById('toolbarCanvas').classList.remove('hidden');
        document.getElementById('fabricWrapper').classList.remove('hidden');
        fCanvas.renderAll();
      } else if (t === 'lowerthird') {
        document.getElementById('tabLowerThird').className = "px-3.5 py-1.5 rounded-lg bg-amber-500/15 text-amber-300 font-semibold transition flex items-center gap-1.5";
        document.getElementById('toolbarLowerThird').classList.remove('hidden');
        document.getElementById('lowerThirdStage').classList.remove('hidden');
      }
    }

    // Fabric Object Selection & Inspector Updates
    fCanvas.on('selection:created', updateInspector);
    fCanvas.on('selection:updated', updateInspector);
    fCanvas.on('selection:cleared', () => {
      document.getElementById('inspectorTitle').innerText = "No Object Selected";
      document.getElementById('inspectorType').innerText = "Click canvas item";
      document.getElementById('textControls').classList.add('hidden');
      document.getElementById('shapeControls').classList.add('hidden');
      document.getElementById('imageControls').classList.add('hidden');
    });

    function updateInspector() {
      const obj = fCanvas.getActiveObject();
      if (!obj) return;

      document.getElementById('inspectorTitle').innerText = obj.name || "Selected Layer";
      document.getElementById('textControls').classList.add('hidden');
      document.getElementById('shapeControls').classList.add('hidden');
      document.getElementById('imageControls').classList.add('hidden');

      if (obj.type === 'i-text' || obj.type === 'text') {
        document.getElementById('inspectorType').innerText = "Live Text";
        document.getElementById('textControls').classList.remove('hidden');
        document.getElementById('propTextContent').value = obj.text;
        document.getElementById('propFontSize').value = obj.fontSize;
        document.getElementById('propFontFamily').value = obj.fontFamily || "Arial";
        document.getElementById('propTextColor').value = obj.fill;
      } else if (obj.type === 'rect') {
        document.getElementById('inspectorType').innerText = "Vector Block";
        document.getElementById('shapeControls').classList.remove('hidden');
        document.getElementById('propShapeFill').value = obj.fill;
        document.getElementById('propShapeStroke').value = obj.stroke || "#000000";
        document.getElementById('propShapeRadius').value = obj.rx || 0;
      } else if (obj.type === 'image') {
        document.getElementById('inspectorType').innerText = "Graphic / Cutout";
        document.getElementById('imageControls').classList.remove('hidden');
      }
    }

    // Property Event Listeners
    document.getElementById('propTextContent').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type.includes('text')) { obj.set('text', e.target.value); fCanvas.renderAll(); updateLayersUI(); }
    });
    document.getElementById('propFontSize').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type.includes('text')) { obj.set('fontSize', parseInt(e.target.value, 10)); fCanvas.renderAll(); }
    });
    document.getElementById('propFontFamily').addEventListener('change', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type.includes('text')) { obj.set('fontFamily', e.target.value); fCanvas.renderAll(); }
    });
    document.getElementById('propTextColor').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type.includes('text')) { obj.set('fill', e.target.value); fCanvas.renderAll(); }
    });
    document.getElementById('propShapeFill').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type === 'rect') { obj.set('fill', e.target.value); fCanvas.renderAll(); }
    });
    document.getElementById('propShapeStroke').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type === 'rect') { obj.set('stroke', e.target.value); fCanvas.renderAll(); }
    });
    document.getElementById('propShapeRadius').addEventListener('input', (e) => {
      const obj = fCanvas.getActiveObject();
      if (obj && obj.type === 'rect') {
        obj.set({ rx: parseInt(e.target.value, 10), ry: parseInt(e.target.value, 10) });
        fCanvas.renderAll();
      }
    });

    // Z-Index Controls
    document.getElementById('btnBringForward').addEventListener('click', () => {
      const obj = fCanvas.getActiveObject();
      if (obj) { fCanvas.bringForward(obj); updateLayersUI(); }
    });
    document.getElementById('btnSendBackward').addEventListener('click', () => {
      const obj = fCanvas.getActiveObject();
      if (obj) { fCanvas.sendBackwards(obj); updateLayersUI(); }
    });

    // Local AI Defringe for Selected Image Layer
    document.getElementById('btnRunAIDefringe').addEventListener('click', async () => {
      const obj = fCanvas.getActiveObject();
      if (!obj || obj.type !== 'image') return;
      document.getElementById('statusText').innerText = "Running local AI neural cutout...";

      const rawB64 = obj.toDataURL();
      try {
        const resp = await fetch('/api/ai_segment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: rawB64 })
        });
        const res = await resp.json();
        if (res.success && res.image) {
          fabric.Image.fromURL(res.image, (newImg) => {
            newImg.set({
              left: obj.left,
              top: obj.top,
              scaleX: obj.scaleX,
              scaleY: obj.scaleY,
              name: (obj.name || "Cutout") + " (AI Clean)"
            });
            fCanvas.remove(obj);
            fCanvas.add(newImg);
            fCanvas.setActiveObject(newImg);
            document.getElementById('statusText').innerText = "AI Cutout Complete!";
            updateLayersUI();
          });
        }
      } catch (err) {
        alert("Could not reach local AI server. Ensure server.py is running on port 8088.");
      }
    });

    // Layers List UI
    function updateLayersUI() {
      const container = document.getElementById('layersList');
      const objects = fCanvas.getObjects();
      document.getElementById('layerCountBadge').innerText = `${objects.length} Layers`;

      container.innerHTML = '';
      objects.slice().reverse().forEach((obj) => {
        const row = document.createElement('div');
        row.className = "flex items-center justify-between p-2.5 rounded-lg bg-[#1c1d24] border border-[#2b2d39] text-xs hover:border-slate-600 transition";
        row.innerHTML = `
          <div class="flex items-center gap-2 truncate">
            <i data-lucide="${obj.type.includes('text') ? 'type' : (obj.type === 'rect' ? 'square' : 'image')}" class="w-3.5 h-3.5 text-amber-400 shrink-0"></i>
            <span class="truncate font-medium text-slate-200">${obj.name || obj.type}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <button onclick="mountToLowerThird(this)" class="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-500/30">Make LT</button>
            <button onclick="deleteLayer(this)" class="text-slate-400 hover:text-red-400"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
          </div>
        `;
        row.onclick = (e) => {
          if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
            fCanvas.setActiveObject(obj);
            fCanvas.renderAll();
          }
        };
        container.appendChild(row);
      });
      lucide.createIcons();
    }

    window.deleteLayer = (btn) => {
      const idx = Array.from(btn.closest('#layersList').children).indexOf(btn.closest('div'));
      const obj = fCanvas.getObjects().slice().reverse()[idx];
      if (obj) { fCanvas.remove(obj); updateLayersUI(); }
    };

    window.mountToLowerThird = (btn) => {
      const idx = Array.from(btn.closest('#layersList').children).indexOf(btn.closest('div'));
      const obj = fCanvas.getObjects().slice().reverse()[idx];
      if (!obj) return;

      switchTab('lowerthird');
      const slot = document.getElementById('ltIconSlot');
      slot.innerHTML = `<img src="${obj.toDataURL()}" class="max-w-full max-h-full object-contain">`;
      document.getElementById('statusText').innerText = `Mounted ${obj.name} as lower-third badge.`;
    };

    // Export SVG
    document.getElementById('btnExportSVG').addEventListener('click', () => {
      const svg = fCanvas.toSVG();
      const blob = new Blob([svg], { type: 'image/svg+xml' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'Miko_Studio_Slicer_Vector.svg';
      a.click();
    });

    // Export PSD
    document.getElementById('btnExportPSD').addEventListener('click', () => {
      const objects = fCanvas.getObjects();
      if (objects.length === 0) return alert('No layers to export. Deconstruct or add elements first.');
      document.getElementById('statusText').innerText = "Generating multi-layer Photoshop PSD...";

      const psdDoc = {
        width: 1280,
        height: 720,
        children: []
      };

      objects.forEach((obj, idx) => {
        if (!obj.visible) return;
        const b = obj.getBoundingRect();
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = Math.max(1, Math.round(b.width));
        tempCanvas.height = Math.max(1, Math.round(b.height));

        const tCtx = tempCanvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
          tCtx.drawImage(img, 0, 0, tempCanvas.width, tempCanvas.height);
        };
        img.src = obj.toDataURL();

        psdDoc.children.push({
          name: obj.name || `Layer_${idx + 1}`,
          top: Math.max(0, Math.round(b.top)),
          left: Math.max(0, Math.round(b.left)),
          bottom: Math.min(720, Math.round(b.top + b.height)),
          right: Math.min(1280, Math.round(b.left + b.width)),
          canvas: tempCanvas,
          opacity: obj.opacity !== undefined ? obj.opacity : 1
        });
      });

      const buffer = agPsd.writePsd(psdDoc);
      const blob = new Blob([buffer], { type: 'application/octet-stream' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'Miko_Studio_Slicer_Master.psd';
      a.click();
      document.getElementById('statusText').innerText = "PSD export complete!";
    });

    // Export 1080p Lower Third PNG
    document.getElementById('btnExport1080pPNG').addEventListener('click', () => {
      const outC = document.createElement('canvas');
      outC.width = 1920;
      outC.height = 1080;
      const oCtx = outC.getContext('2d');

      const bannerX = 140;
      const bannerY = 840;
      const bannerW = 920;
      const bannerH = 120;

      oCtx.fillStyle = '#0f172a';
      oCtx.fillRect(bannerX, bannerY, bannerW, bannerH);
      oCtx.strokeStyle = '#f59e0b';
      oCtx.lineWidth = 3;
      oCtx.strokeRect(bannerX, bannerY, bannerW, bannerH);

      oCtx.fillStyle = '#f59e0b';
      oCtx.fillRect(bannerX, bannerY - 35, 460, 35);
      oCtx.fillStyle = '#0f172a';
      oCtx.font = "900 16px 'Segoe UI', system-ui, sans-serif";
      oCtx.fillText(document.getElementById('ltRoleDisplay').innerText, bannerX + 25, bannerY - 12);

      oCtx.fillStyle = '#ffffff';
      oCtx.font = "bold 44px 'Segoe UI', system-ui, sans-serif";
      oCtx.fillText(document.getElementById('ltNameDisplay').innerText, bannerX + 130, bannerY + 75);

      const imgElem = document.getElementById('ltIconSlot').querySelector('img');
      if (imgElem) {
        oCtx.drawImage(imgElem, bannerX + 15, bannerY + 15, 90, 90);
      }

      const a = document.createElement('a');
      a.href = outC.toDataURL('image/png');
      a.download = 'Miko_Studio_LowerThird_1080p.png';
      a.click();
    });
  </script>
</body>
</html>
"""

with open(os.path.join(APP_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)
print("    [+] index.html written.")

if os.path.exists(INSTALL_DIR):
    print(f"[*] Synchronizing to {INSTALL_DIR}...")
    shutil.copy2(os.path.join(APP_DIR, "index.html"), os.path.join(INSTALL_DIR, "index.html"))
    shutil.copy2(os.path.join(APP_DIR, "icon.ico"), os.path.join(INSTALL_DIR, "icon.ico"))
    print("    [+] Synced index.html and icon.ico to Program Files directory.")

print("\n[SUCCESS] Miko Studio Slicer architecture updated successfully!")
