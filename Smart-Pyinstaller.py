import sys
import io
import shutil
import subprocess

from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# -------- Colors --------
USE_COLOR = sys.stdout.isatty()
GREEN  = '\033[92m' if USE_COLOR else ''
YELLOW = '\033[93m' if USE_COLOR else ''
RED    = '\033[91m' if USE_COLOR else ''
BLUE   = '\033[94m' if USE_COLOR else ''
RESET  = '\033[0m'  if USE_COLOR else ''
# ----------------------
def info(msg):  print(f"{BLUE}[i]{RESET} {msg}")
def ok(msg):    print(f"{GREEN}[✓]{RESET} {msg}")
def warn(msg):  print(f"{YELLOW}[!]{RESET} {msg}")
def error(msg): print(f"{RED}[✗]{RESET} {msg}")

# ---------- ICON HANDLING ----------
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def crop_to_square(img):
    w, h = img.size
    if w == h:
        return img
    side = min(w, h)
    left = (w - side)//2; top = (h - side)//2
    return img.crop((left, top, left+side, top+side))

def find_and_convert_icon(base_dir):
    
    ico_files = [f for f in base_dir.glob("*.ico") if f.name != "temp_icon.ico"]
    if ico_files:
        return ico_files[0], False
    images = []
    for ext in ["*.png","*.jpg","*.jpeg","*.bmp","*.webp"]:
        images.extend(base_dir.glob(ext))
    if not images:
        return None, False
    if not PIL_AVAILABLE:
        warn(f"Found image {images[0].name}, but Pillow is missing. Run: pip install Pillow")
        return None, False
        
    img_path = images[0]
    info(f"Converting {img_path.name} to .ico...")
    try:
        ico_path = base_dir / "temp_icon.ico"
        with Image.open(img_path) as img:
            square = crop_to_square(img)
            sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
            resample = getattr(Image, 'Resampling', Image).LANCZOS
            imgs = [square.resize(s, resample) for s in sizes]
            imgs[0].save(ico_path, format="ICO", sizes=[s for s in sizes],
                         append_images=imgs[1:])
        return ico_path, True
    except Exception as e:
        warn(f"Icon conversion failed: {e}")
        return None, False

# ---------- CLEANUP ----------
def cleanup(base_dir, exe_name, temp_icon, keep_spec=True):
    #Icon
    if temp_icon and temp_icon.exists():
        try: temp_icon.unlink()
        except: pass
    #Build        
    build_dir = base_dir / "build"
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
        except Exception as e:
            warn(f"Cleanup failed for build/ folder (it may be locked by antivirus or system): {e}")
    #Spec
    spec_file = base_dir / f"{exe_name}.spec"
    if keep_spec:
        if spec_file.exists():
            info(f".spec-file saved: {spec_file}")
    else:
        if spec_file.exists():
            try:
                spec_file.unlink()
            except Exception as e:
                warn(f"Failed to remove {exe_name}.spec: {e}")           

# ---------- MAIN ----------
def main():
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN}   Smart-PyInstaller Builder       {RESET}")
    print(f"{GREEN}====================================={RESET}\n")

    base_dir = Path.cwd().resolve()
    is_windows = sys.platform == 'win32'
    info(f"Project folder: {base_dir}")

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        error("PyInstaller is not installed! Install it: pip install pyinstaller")
        input("\nPress Enter to exit...")
        return 1
    
    main_candidates = [f for f in base_dir.glob("*.py") if f.stem.lower() == "main"]
    if main_candidates:
        script = main_candidates[0]
        info(f"Found main script: {script.name}")
    else:
        all_py = [f for f in base_dir.glob("*.py") if f.resolve() != Path(__file__).resolve()]
        if not all_py:
            error("No .py files found!")
            input("\nPress Enter to exit...")
            return 1
        print("Available scripts:")
        for i, f in enumerate(all_py, 1):
            print(f"  {i}. {f.name}")
        choice = input("Enter the number of the script to build: ").strip()
        try:
            script = all_py[int(choice)-1]
        except:
            warn("Invalid choice – using the first script.")
            script = all_py[0]

    # EXE name
    default_name = script.stem
    exe_name = input(f"EXE name (Enter = {default_name}): ").strip() or default_name
    exe_name = exe_name.strip(' .')
    if not exe_name:
        exe_name = default_name      
    for ch in r'\/:*?"<>|':
        exe_name = exe_name.replace(ch, '_')

    # Console mode
    console = input("Show console window? (Y/N): ").strip().lower() == 'y'
    # Administrator privileges
    admin = input("Request administrator privileges on launch? (Y/N): ").strip().lower() == 'y'
    # Icon
    icon_path, is_temp = find_and_convert_icon(base_dir)
    #Spec delete
    keep_spec = input("Delete temporary .spec file after build? (Y/N): ").strip().lower() == 'y'
    
    # Build the PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        f"--name={exe_name}"
    ]
    cmd += ["--noconsole"] if not console else []
    if icon_path:
        cmd.extend(["--icon", str(icon_path)])        
    if admin and not is_windows:
        warn("--uac-admin skipped (only available on Windows)")
    cmd += ["--uac-admin"] if (admin and is_windows) else []

    # Auto-add --collect-all for customtkinter if detected
    with open(script, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if "customtkinter" in content:
        cmd.append("--collect-all=customtkinter")
        info("customtkinter detected – added --collect-all")

    cmd.append(str(script))

    dist_dir = base_dir / "dist"
    dist_dir.mkdir(exist_ok=True)

    # Run PyInstaller
    info("Running PyInstaller...")
    success = False
    try:
        subprocess.run(cmd, check=True)
        success = True
    except subprocess.CalledProcessError:
        success = False

    # Cleanup temporary files
    cleanup(base_dir, exe_name, icon_path if is_temp else None, keep_spec=keep_spec)

    # Result
    print()
    if success:
        exe_suffix = '.exe' if is_windows else ''
        exe_path = dist_dir / f"{exe_name}{exe_suffix}"
        ok(f"Build successful! File: {exe_path}")
    else:
        error("Build failed. Check the error messages above.")

    input("\nPress Enter to exit...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
