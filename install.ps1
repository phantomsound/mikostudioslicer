Add-Type -AssemblyName System.Windows.Forms;
Add-Type -AssemblyName System.Drawing;

[System.Windows.Forms.Application]::EnableVisualStyles();

$form = New-Object System.Windows.Forms.Form;
$form.Text = "MikoStudioSlicer Setup";
$form.Size = New-Object System.Drawing.Size(520, 450);$form.StartPosition = "CenterScreen";
$form.FormBorderStyle = "FixedDialog";
$form.MaximizeBox =$false;
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42);$form.ForeColor = [System.Drawing.Color]::White;

# Title
$title = New-Object System.Windows.Forms.Label;
$title.Text = "MikoStudioSlicer Setup";
$title.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold);
$title.Location = New-Object System.Drawing.Point(20, 15);
$title.Size = New-Object System.Drawing.Size(460, 28);$title.ForeColor = [System.Drawing.Color]::FromArgb(245, 158, 11);
$form.Controls.Add($title);

# Install Path Label & Box
$lblPath = New-Object System.Windows.Forms.Label;
$lblPath.Text = "Install Folder:";
$lblPath.Location = New-Object System.Drawing.Point(20, 52);$lblPath.Size = New-Object System.Drawing.Size(460, 18);
$form.Controls.Add($lblPath);

$txtPath = New-Object System.Windows.Forms.TextBox;
$txtPath.Text = "C:\Program Files (x86)\Miko Studio Slicer";
$txtPath.Location = New-Object System.Drawing.Point(20, 72);$txtPath.Size = New-Object System.Drawing.Size(370, 24);
$txtPath.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59);$txtPath.ForeColor = [System.Drawing.Color]::White;
$form.Controls.Add($txtPath);

$btnBrowse = New-Object System.Windows.Forms.Button;
$btnBrowse.Text = "Browse...";
$btnBrowse.Location = New-Object System.Drawing.Point(400, 70);$btnBrowse.Size = New-Object System.Drawing.Size(80, 28);
$btnBrowse.BackColor = [System.Drawing.Color]::FromArgb(51, 65, 85);$btnBrowse.ForeColor = [System.Drawing.Color]::White;
$btnBrowse.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat;
$btnBrowse.Add_Click({$fbd = New-Object System.Windows.Forms.FolderBrowserDialog;
    $fbd.SelectedPath =$txtPath.Text;
    if ($fbd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { 
        $txtPath.Text =$fbd.SelectedPath; 
    };
});
$form.Controls.Add($btnBrowse);

# Options Box
$grp = New-Object System.Windows.Forms.GroupBox;
$grp.Text = "Installation Options";
$grp.Location = New-Object System.Drawing.Point(20, 115);
$grp.Size = New-Object System.Drawing.Size(460, 195);$grp.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225);
$form.Controls.Add($grp);

$chkService = New-Object System.Windows.Forms.CheckBox;
$chkService.Text = "Install local service with auto-port detection (Port 8088+)";
$chkService.Checked =$true;
$chkService.Location = New-Object System.Drawing.Point(15, 28);$chkService.Size = New-Object System.Drawing.Size(430, 24);
$grp.Controls.Add($chkService);

$chkStartup = New-Object System.Windows.Forms.CheckBox;
$chkStartup.Text = "Start local service automatically when Windows boots";
$chkStartup.Checked =$true;
$chkStartup.Location = New-Object System.Drawing.Point(15, 62);$chkStartup.Size = New-Object System.Drawing.Size(430, 24);
$grp.Controls.Add($chkStartup);

$chkDesktop = New-Object System.Windows.Forms.CheckBox;
$chkDesktop.Text = "Create Desktop Shortcut";
$chkDesktop.Checked =$true;
$chkDesktop.Location = New-Object System.Drawing.Point(15, 96);$chkDesktop.Size = New-Object System.Drawing.Size(430, 24);
$grp.Controls.Add($chkDesktop);

$chkStart = New-Object System.Windows.Forms.CheckBox;
$chkStart.Text = "Create Start Menu entry (Ready to Pin to Taskbar)";
$chkStart.Checked =$true;
$chkStart.Location = New-Object System.Drawing.Point(15, 130);$chkStart.Size = New-Object System.Drawing.Size(430, 24);
$grp.Controls.Add($chkStart);

# Install Action
$btnInstall = New-Object System.Windows.Forms.Button;
$btnInstall.Text = "Install Now";
$btnInstall.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold);
$btnInstall.Location = New-Object System.Drawing.Point(320, 340);
$btnInstall.Size = New-Object System.Drawing.Size(160, 40);$btnInstall.BackColor = [System.Drawing.Color]::FromArgb(245, 158, 11);
$btnInstall.ForeColor = [System.Drawing.Color]::FromArgb(15, 23, 42);$btnInstall.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat;
$form.Controls.Add($btnInstall);

$status = New-Object System.Windows.Forms.Label;
$status.Location = New-Object System.Drawing.Point(20, 350);
$status.Size = New-Object System.Drawing.Size(290, 25);$status.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184);
$form.Controls.Add($status);

$btnInstall.Add_Click({
    $btnInstall.Enabled =$false;
    $targetDir =$txtPath.Text.Trim();
    $sourceDir =$PSScriptRoot;

    try {
        $status.Text = "Copying files...";
        $form.Refresh();

        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null;
        };

        # Grant local Users full write permissions on this folder so non-admin execution works
        Start-Process "icacls" -ArgumentList "`"$targetDir`"", "/grant", "Users:(OI)(CI)M", "/T", "/Q" -Wait -NoNewWindow;

        $copyList = @("index.html", "requirements.txt", "setup_illustrator.jsx", "slicer_engine.py", "server.py", "uninstall.ps1");
        foreach ($item in $copyList) {$s = Join-Path $sourceDir$item;
            if (Test-Path $s) { Copy-Item $s -Destination$targetDir -Force; };
        };

        $status.Text = "Configuring Python virtual environment...";
        $form.Refresh();

        # Locate Python
        $pythonExe = "python.exe";
        if (-not (Get-Command "python.exe" -ErrorAction SilentlyContinue)) {
            if (Get-Command "py.exe" -ErrorAction SilentlyContinue) {
                $pythonExe = "py.exe";
            } else {
                throw "Python was not found in system PATH. Please ensure Python is installed with 'Add Python to PATH' checked.";
            }
        };

        $venv = Join-Path$targetDir "venv";
        if (-not (Test-Path $venv)) {
            Start-Process -FilePath $pythonExe -ArgumentList "-m", "venv", "`"$venv`"" -Wait -NoNewWindow;
        };

        $pip = Join-Path$venv "Scripts\pip.exe";
        $req = Join-Path$targetDir "requirements.txt";
        if (Test-Path $pip) {
            Start-Process -FilePath $pip -ArgumentList "install", "-r", "`"$req`"" -Wait -NoNewWindow;
        };

        $pythonw = Join-Path$venv "Scripts\pythonw.exe";
        if (-not (Test-Path $pythonw)) {$pythonw = "pythonw.exe"; };
        $serverPy = Join-Path$targetDir "server.py";

        $wsh = New-Object -ComObject WScript.Shell;

        if ($chkDesktop.Checked) {$desk = [System.Environment]::GetFolderPath("Desktop");
            $sc = $wsh.CreateShortcut((Join-Path$desk "MikoStudioSlicer.lnk"));
            $sc.TargetPath =$pythonw;
            $sc.Arguments = "`"$serverPy`" --launch";
            $sc.WorkingDirectory =$targetDir;
            $sc.Description = "MikoStudioSlicer Production Studio";
            $sc.Save();
        };

        if ($chkStart.Checked) {$smDir = Join-Path ([System.Environment]::GetFolderPath("StartMenu")) "Programs\MikoStudioSlicer";
            if (-not (Test-Path $smDir)) { New-Item -ItemType Directory -Path $smDir -Force \vert{} Out-Null; };$sc = $wsh.CreateShortcut((Join-Path$smDir "MikoStudioSlicer.lnk"));
            $sc.TargetPath =$pythonw;
            $sc.Arguments = "`"$serverPy`" --launch";
            $sc.WorkingDirectory =$targetDir;
            $sc.Description = "MikoStudioSlicer Production Studio";
            $sc.Save();
        };

        if ($chkStartup.Checked) {$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run";
            $cmd = "`"$pythonw`" `"$serverPy`"";
            Set-ItemProperty -Path $reg -Name "MikoStudioSlicerService" -Value $cmd;
        };

        if ($chkService.Checked) {
            Start-Process -FilePath $pythonw -ArgumentList "`"$serverPy`" --launch" -WorkingDirectory $targetDir;
        };

        [System.Windows.Forms.MessageBox]::Show("MikoStudioSlicer installed successfully.`n`nInstalled to: $targetDir", "Setup Complete", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information);
        $form.Close();
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("Installation failed with error:`n`n$($_.Exception.Message)", "Install Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error);
        $btnInstall.Enabled =$true;
        $status.Text = "Installation failed.";
    }
});

$form.ShowDialog() | Out-Null;
