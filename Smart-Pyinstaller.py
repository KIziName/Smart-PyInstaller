import sys
import os
import io
import shutil
import subprocess
from pathlib import Path

# Fix console encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class Colors:
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    BLUE = '\033[94m'; RESET = '\033[0m'
    if not sys.stdout.isatty():
        GREEN = YELLOW = RED = BLUE = RESET = ''

def info(msg):  print(f"{Colors.BLUE}[i]{Colors.RESET} {msg}")
def ok(msg):    print(f"{Colors.GREEN}[✓]{Colors.RESET} {msg}")
def warn(msg):  print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")
def error(msg): print(f"{Colors.RED}[✗]{Colors.RESET} {msg}")

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
    """
    Looks for a .ico file in the project folder.
    If none found, converts the first image (PNG/JPG/etc.) to .ico.
    Returns (icon_path, is_temp) where is_temp=True if a temporary file was created.
    """
    ico_files = list(base_dir.glob("*.ico"))
    if ico_files:
        return ico_files[0], False
    if not PIL_AVAILABLE:
        return None, False
    images = []
    for ext in ["*.png","*.jpg","*.jpeg","*.bmp","*.webp"]:
        images.extend(base_dir.glob(ext))
    if not images:
        return None, False
    img_path = images[0]
    info(f"Converting {img_path.name} to .ico...")
    try:
        ico_path = base_dir / "temp_icon.ico"
        with Image.open(img_path) as img:
            square = crop_to_square(img)
            sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
            imgs = [square.resize(s, Image.Resampling.LANCZOS) for s in sizes]
            imgs[0].save(ico_path, format="ICO", sizes=[s for s in sizes],
                         append_images=imgs[1:])
        return ico_path, True
    except Exception as e:
        warn(f"Icon conversion failed: {e}")
        return None, False

# ---------- CLEANUP ----------
def cleanup(base_dir, exe_name, temp_icon):
    """Remove temporary build files and the .spec file."""
    if temp_icon and temp_icon.exists():
        try: temp_icon.unlink()
        except: pass
    build_dir = base_dir / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    spec_file = base_dir / f"{exe_name}.spec"
    if spec_file.exists():
        spec_file.unlink()

# ---------- MAIN ----------
def main():
    print(f"{Colors.GREEN}====================================={Colors.RESET}")
    print(f"{Colors.GREEN}   Smart-PyInstaller Builder       {Colors.RESET}")
    print(f"{Colors.GREEN}====================================={Colors.RESET}\n")

    base_dir = Path.cwd().resolve()
    info(f"Project folder: {base_dir}")

    
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
    name_input = input(f"EXE name (Enter = {default_name}): ").strip()
    exe_name = name_input if name_input else default_name
    # Remove invalid characters for Windows filenames
    for ch in r'\/:*?"<>|':
        exe_name = exe_name.replace(ch, '_')

    # Console mode
    console = input("Show console window? (y/N): ").strip().lower() == 'y'

    # Administrator privileges
    admin = input("Request administrator privileges on launch? (y/N): ").strip().lower() == 'y'

    # Icon
    icon_path, is_temp = find_and_convert_icon(base_dir)

    # Build the PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        f"--name={exe_name}"
    ]
    if not console:
        cmd.append("--noconsole")
    if icon_path:
        cmd.extend(["--icon", str(icon_path)])
    if admin:
        cmd.append("--uac-admin")

    # Auto-add --collect-all for customtkinter if detected
    with open(script, 'r', encoding='utf-8') as f:
        content = f.read()
    if "customtkinter" in content:
        cmd.append("--collect-all=customtkinter")
        info("customtkinter detected – added --collect-all")

    cmd.append(str(script))

    # Clean the dist folder
    dist_dir = base_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    dist_dir.mkdir(exist_ok=True)

    # Run PyInstaller
    info("Running PyInstaller...")
    success = False
    try:
        subprocess.run(cmd, check=True)
        success = True
    except subprocess.CalledProcessError:
        success = False
    except FileNotFoundError:
        error("PyInstaller not found! Install it: pip install pyinstaller")

    # Cleanup temporary files
    cleanup(base_dir, exe_name, icon_path if is_temp else None)

    # Result
    print()
    if success:
        exe_path = dist_dir / f"{exe_name}.exe"
        ok(f"Build successful! File: {exe_path}")
    else:
        error("Build failed. Check the error messages above.")

    input("\nPress Enter to exit...")
    return 0

if __name__ == "__main__":
    sys.exit(main())