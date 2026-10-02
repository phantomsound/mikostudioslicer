import ctypes, filecmp, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Miko Studio Slicer")
FILES = ["index.html", "server.py", "requirements.txt", "icon.ico", "sample_concept.png",
         "setup_illustrator.jsx", "uninstall.ps1", "update_studio.py"]


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def main():
    if not is_admin():
        args = " ".join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, None, 1)
        return
    if os.path.isdir(os.path.join(REPO, ".git")):
        subprocess.run(["git", "-C", REPO, "pull", "--ff-only"])
    if not os.path.isdir(DEST):
        print("Miko Studio Slicer is not installed. Run install.bat first.")
        return
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | "
                    "Where-Object { $_.CommandLine -like '*Miko Studio Slicer*' } | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"])
    reqs_changed = not os.path.exists(os.path.join(DEST, "requirements.txt")) or not filecmp.cmp(
        os.path.join(REPO, "requirements.txt"), os.path.join(DEST, "requirements.txt"), shallow=False)
    for n in FILES:
        shutil.copy2(os.path.join(REPO, n), os.path.join(DEST, n))
    vpy = os.path.join(DEST, "venv", "Scripts", "python.exe")
    if reqs_changed:
        subprocess.run([vpy, "-m", "pip", "install", "-r", os.path.join(DEST, "requirements.txt")])
    subprocess.Popen([os.path.join(DEST, "venv", "Scripts", "pythonw.exe"),
                      os.path.join(DEST, "server.py"), "--launch"], cwd=DEST,
                     creationflags=0x00000008 | 0x00000200)
    print("Miko Studio Slicer updated and relaunched.")
    input("Press Enter to close.")


if __name__ == "__main__":
    main()
