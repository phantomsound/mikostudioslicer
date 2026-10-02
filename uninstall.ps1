$App = 'Miko Studio Slicer';
$Dest = Join-Path ${env:ProgramFiles(x86)} $App;
$me = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent();
if (-not $me.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"";
    exit;
};
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like '*Miko Studio Slicer*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; };
foreach ($d in @([Environment]::GetFolderPath('CommonDesktopDirectory'),[Environment]::GetFolderPath('CommonPrograms'))) {
    Remove-Item (Join-Path $d "$App.lnk") -Force -ErrorAction SilentlyContinue;
};
Remove-Item (Join-Path $env:TEMP 'MikoStudioSlicer.port') -Force -ErrorAction SilentlyContinue;
Start-Process cmd.exe -ArgumentList "/c timeout /t 2 /nobreak >nul & rmdir /s /q `"$Dest`"" -WindowStyle Hidden;
