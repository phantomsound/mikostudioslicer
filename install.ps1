Add-Type -AssemblyName System.Windows.Forms;
Add-Type -AssemblyName System.Drawing;
[System.Windows.Forms.Application]::EnableVisualStyles();
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;
$App = 'Miko Studio Slicer';
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path;
$Dest = Join-Path ${env:ProgramFiles(x86)} $App;
$Files = @('index.html','server.py','requirements.txt','icon.ico','sample_concept.png','setup_illustrator.jsx','uninstall.ps1','update_studio.py');
$Vendor = @(
    @('tailwind.js','https://cdn.tailwindcss.com'),
    @('fabric.min.js','https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js'),
    @('jszip.min.js','https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js'),
    @('ag-psd.js','https://cdn.jsdelivr.net/npm/ag-psd/dist/bundle.js'),
    @('lucide.min.js','https://cdn.jsdelivr.net/npm/lucide@0.383.0/dist/umd/lucide.min.js')
);

$f = New-Object System.Windows.Forms.Form;
$f.Text = "$App Installer";
$f.Size = New-Object System.Drawing.Size(660,470);
$f.StartPosition = 'CenterScreen';
$f.FormBorderStyle = 'FixedDialog';
$f.MaximizeBox = $false;
$f.BackColor = [System.Drawing.ColorTranslator]::FromHtml('#121316');
$f.ForeColor = [System.Drawing.ColorTranslator]::FromHtml('#e6e7ea');
try { $f.Icon = New-Object System.Drawing.Icon((Join-Path $Src 'icon.ico')); } catch { };
$lbl = New-Object System.Windows.Forms.Label;
$lbl.Text = "Install $App to:`r`n$Dest";
$lbl.SetBounds(20,16,610,44);
$lbl.Font = New-Object System.Drawing.Font('Segoe UI',10);
$bar = New-Object System.Windows.Forms.ProgressBar;
$bar.SetBounds(20,68,610,22);
$log = New-Object System.Windows.Forms.TextBox;
$log.Multiline = $true;
$log.ReadOnly = $true;
$log.ScrollBars = 'Vertical';
$log.SetBounds(20,100,610,270);
$log.BackColor = [System.Drawing.ColorTranslator]::FromHtml('#1a1c21');
$log.ForeColor = [System.Drawing.ColorTranslator]::FromHtml('#e6e7ea');
$log.Font = New-Object System.Drawing.Font('Consolas',9);
$btn = New-Object System.Windows.Forms.Button;
$btn.Text = 'Install';
$btn.SetBounds(510,382,120,36);
$btn.FlatStyle = 'Flat';
$btn.BackColor = [System.Drawing.ColorTranslator]::FromHtml('#d4a64a');
$btn.ForeColor = [System.Drawing.ColorTranslator]::FromHtml('#121316');
$f.Controls.AddRange(@($lbl,$bar,$log,$btn));

function Log($m) { $log.AppendText("$m`r`n"); [System.Windows.Forms.Application]::DoEvents(); };
function Step($p, $m) { $bar.Value = $p; Log $m; };
function Run($exe, $argList) {
    $old = $ErrorActionPreference;
    $ErrorActionPreference = 'Continue';
    & $exe @argList 2>&1 | ForEach-Object { Log "$_"; };
    $code = $LASTEXITCODE;
    $ErrorActionPreference = $old;
    if ($code -ne 0) { throw "$exe exited with code $code"; };
};
function Find-Python {
    $cands = @(@('py','-3.12'),@('py','-3.13'),@('py','-3.11'),@('py','-3.10'),@('python'));
    foreach ($c in $cands) {
        try {
            $exe = $c[0];
            $rest = @($c | Select-Object -Skip 1);
            $out = & $exe @rest -c "import sys;print(sys.executable if (3,10)<=sys.version_info[:2]<=(3,13) else '')" 2>$null;
            if ($out -and (Test-Path "$out")) { return "$out"; };
        } catch { };
    };
    return $null;
};

$btn.Add_Click({
    $btn.Enabled = $false;
    try {
        Step 3 'Stopping running instances...';
        Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like '*Miko Studio Slicer*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; };
        Step 8 'Copying application files...';
        New-Item -ItemType Directory -Force -Path $Dest | Out-Null;
        New-Item -ItemType Directory -Force -Path (Join-Path $Dest 'vendor') | Out-Null;
        foreach ($n in $Files) { Copy-Item -Force (Join-Path $Src $n) (Join-Path $Dest $n); };
        Step 14 'Locating Python 3.10-3.13...';
        $py = Find-Python;
        if (-not $py) {
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Python is missing and winget is unavailable. Install Python 3.12 manually.'; };
            Step 16 'Installing Python 3.12 via winget...';
            Run 'winget' @('install','-e','--id','Python.Python.3.12','--scope','machine','--silent','--accept-package-agreements','--accept-source-agreements');
            $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User');
            $py = Find-Python;
            if (-not $py) { throw 'Python installation failed.'; };
        };
        Log "Using $py";
        Step 30 'Creating virtual environment...';
        Run $py @('-m','venv',(Join-Path $Dest 'venv'));
        $vpy = Join-Path $Dest 'venv\Scripts\python.exe';
        Step 38 'Installing Python dependencies (rembg, pillow, onnxruntime)...';
        Run $vpy @('-m','pip','install','--upgrade','pip');
        Run $vpy @('-m','pip','install','-r',(Join-Path $Dest 'requirements.txt'));
        Step 70 'Downloading frontend libraries to vendor...';
        foreach ($v in $Vendor) {
            $out = Join-Path $Dest ('vendor\' + $v[0]);
            Invoke-WebRequest -Uri $v[1] -OutFile $out -UseBasicParsing;
            if ((Get-Item $out).Length -lt 1000) { throw "Download failed: $($v[1])"; };
            Log "  $($v[0])";
        };
        Step 80 'Caching u2net model for offline use...';
        $env:U2NET_HOME = Join-Path $Dest 'models';
        Run $vpy @('-c',"from rembg import new_session; new_session('u2net')");
        Step 95 'Creating shortcuts...';
        $ws = New-Object -ComObject WScript.Shell;
        foreach ($d in @([Environment]::GetFolderPath('CommonDesktopDirectory'),[Environment]::GetFolderPath('CommonPrograms'))) {
            $s = $ws.CreateShortcut((Join-Path $d "$App.lnk"));
            $s.TargetPath = Join-Path $Dest 'venv\Scripts\pythonw.exe';
            $s.Arguments = "`"$(Join-Path $Dest 'server.py')`" --launch";
            $s.WorkingDirectory = $Dest;
            $s.IconLocation = (Join-Path $Dest 'icon.ico');
            $s.Description = $App;
            $s.Save();
        };
        $bar.Value = 100;
        Log "Done. Launch $App from the desktop shortcut.";
        $btn.Text = 'Close';
        $btn.Add_Click({ $f.Close(); });
    } catch {
        Log "ERROR: $($_.Exception.Message)";
    };
    $btn.Enabled = $true;
});
[void]$f.ShowDialog();
