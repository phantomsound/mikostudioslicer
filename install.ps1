Add-Type -AssemblyName System.Windows.Forms, System.Drawing;
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
$tb.Text = "C:\\Program Files (x86)\\Miko Studio Slicer";
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
            $sf = "$src\$fn";
            if (Test-Path -LiteralPath $sf) { Copy-Item -LiteralPath $sf -Destination $dst -Force; };
        };
        $st.Text = "Configuring Python virtual environment..."; $f.Refresh();
        $py = if (Get-Command "python.exe" -ErrorAction SilentlyContinue) { "python.exe" } elseif (Get-Command "py.exe" -ErrorAction SilentlyContinue) { "py.exe" } else { throw "Python not found in system PATH."; };
        $v = "$dst\venv";
        if (-not (Test-Path -LiteralPath $v)) { Start-Process $py -ArgumentList "-m", "venv", "`"$v`"" -Wait -NoNewWindow; };
        $pip = "$v\Scripts\pip.exe"; $req = "$dst\requirements.txt";
        if (Test-Path -LiteralPath $pip) { Start-Process $pip -ArgumentList "install", "-r", "`"$req`"" -Wait -NoNewWindow; };
        $pyw = "$v\Scripts\pythonw.exe"; if (-not (Test-Path -LiteralPath $pyw)) { $pyw = "pythonw.exe"; };
        $srv = "$dst\server.py";
        $iconPath = "$dst\icon.ico";
        $wsh = New-Object -ComObject WScript.Shell;
        if ($c3.Checked) {
            $desk = [Environment]::GetFolderPath("Desktop");
            $sc = $wsh.CreateShortcut("$desk\Miko Studio Slicer.lnk");
            $sc.TargetPath = $pyw;
            $sc.Arguments = "`"$srv`" --launch";
            $sc.WorkingDirectory = $dst;
            $sc.Description = "Miko Studio Slicer Production Studio";
            if (Test-Path -LiteralPath $iconPath) { $sc.IconLocation = "$iconPath,0"; };
            $sc.Save();
        };
        $sm = [Environment]::GetFolderPath("StartMenu");
        $smd = "$sm\Programs\Miko Studio Slicer";
        if (-not (Test-Path -LiteralPath $smd)) { New-Item -ItemType Directory -Path $smd -Force | Out-Null; };
        $scSm = $wsh.CreateShortcut("$smd\Miko Studio Slicer.lnk");
        $scSm.TargetPath = $pyw;
        $scSm.Arguments = "`"$srv`" --launch";
        $scSm.WorkingDirectory = $dst;
        $scSm.Description = "Miko Studio Slicer Production Studio";
        if (Test-Path -LiteralPath $iconPath) { $scSm.IconLocation = "$iconPath,0"; };
        $scSm.Save();
        if ($c2.Checked) {
            Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "MikoStudioSlicerService" -Value "`"$pyw`" `"$srv`"";
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
