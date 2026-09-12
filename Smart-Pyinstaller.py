from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import time

from dataclasses import dataclass
from pathlib import Path

ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
IMAGE_EXTS = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]
IGNORED_DIRS = {'.git', 'venv', '.venv', 'env', '.env','build', 'dist', '__pycache__', 'site-packages'}


@dataclass
class BuildOptions:
    console: bool = False
    admin: bool = False
    keep_spec: bool = False
    include_numpy: bool = False
    include_pil: bool = False

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

USE_COLOR = sys.stdout.isatty()
GREEN = '\033[92m' if USE_COLOR else ''
YELLOW = '\033[93m' if USE_COLOR else ''
RED = '\033[91m' if USE_COLOR else ''
BLUE = '\033[94m' if USE_COLOR else ''
RESET = '\033[0m' if USE_COLOR else ''

def info(msg): print(f"{BLUE}[i]{RESET} {msg}")
def ok(msg): print(f"{GREEN}[✓]{RESET} {msg}")
def warn(msg): print(f"{YELLOW}[!]{RESET} {msg}")
def error(msg): print(f"{RED}[✗]{RESET} {msg}")

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
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))
    

def find_and_convert_icon(base_dir):
    ico_files = [f for f in base_dir.glob("*.ico") if f.name != "temp_icon.ico"]
    if ico_files:
        return ico_files[0], False

    images = []
    for ext in IMAGE_EXTS:
        images.extend(base_dir.glob(ext))

    if not images:
        return None, False

    if not PIL_AVAILABLE:
        warn(f"Found image {images[0].name}, but Pillow is missing. "
             "Run: pip install Pillow")
        return None, False

    img_path = images[0]
    info(f"Converting {img_path.name} to .ico...")
    try:
        ico_path = base_dir / "temp_icon.ico"
        with Image.open(img_path) as img:
            square = crop_to_square(img)
            square.save(ico_path, format="ICO", sizes=ICON_SIZES)
        return ico_path, True
    except Exception as e:
        warn(f"Icon conversion failed: {e}")
        return None, False
        

def find_used_modules(base_dir: Path, names: set[str]) -> set[str]:
    found = set()
    self_name = Path(__file__).name
    for py_file in base_dir.rglob("*.py"):
        rel_parts = py_file.relative_to(base_dir).parts
        dir_parts = rel_parts[:-1]
        if any(part in IGNORED_DIRS for part in dir_parts):
            continue
        if py_file.name == self_name:
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for name in names:
            if re.search(
                rf'^\s*(?:import\s+{re.escape(name)}(?:\s|$|\.)|'
                rf'from\s+{re.escape(name)}(?:\s|\.)\s+import)',
                content,
                re.MULTILINE
             ):
                found.add(name)
    return found
    
    
def ask_build_options(base_dir, used_modules):
    options = BuildOptions()
    options.console = input("Show console window? (y/N, Enter: N): ").strip().lower() == 'y'
    options.admin = input("Request administrator privileges on launch? (y/N, Enter: N): ").strip().lower() == 'y'
    options.keep_spec = input("Keep .spec file after build for later use? (y/N, Enter: N): ").strip().lower() == 'y'
    options.include_numpy = input("Include NumPy explicitly? (y/N, Enter: N): ").strip().lower() == 'y'

    if 'PIL' in used_modules:
        warn("PIL (Pillow) imports detected in your project source code.")
    options.include_pil = input("Include PIL (Pillow) in the build? (y/N, Enter: N): ").strip().lower() == 'y'

    return options

def cleanup(base_dir, exe_name, temp_icon, keep_spec=True):
    if temp_icon and temp_icon.exists():
        try:
            temp_icon.unlink()
        except Exception:
            pass

    build_dir = base_dir / "build"
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
        except Exception as e:
            warn(f"Cleanup failed for build/ folder "
                f"(it may be locked by antivirus or system): {e}"
            )
            
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
                

def main():
    print(f"{GREEN}====================================={RESET}")
    print(f"{GREEN}   Smart-PyInstaller Builder       {RESET}")
    print(f"{GREEN}====================================={RESET}\n")

    start_time = time.time()
    base_dir = Path.cwd().resolve()
    is_windows = sys.platform == 'win32'
    info(f"Project folder: {base_dir}")

    try:
        import PyInstaller
        ver = getattr(PyInstaller, '__version__', 'unknown')
        info(f"PyInstaller version: {ver}")
    except ImportError:
        error("PyInstaller is not installed! Install it: pip install pyinstaller")
        input("\nPress Enter to exit...")
        return 5

    main_candidates = [f for f in base_dir.glob("*.py") if f.stem.lower() == "main"]
    if main_candidates:
        script = main_candidates[0]
        info(f"Found main script: {script.name}")
    else:
        all_py = [
            f for f in base_dir.glob("*.py")
            if f.resolve() != Path(__file__).resolve()
        ]
        if not all_py:
            error("No .py files found!")
            input("\nPress Enter to exit...")
            return 10

        print("Available scripts:")
        for i, f in enumerate(all_py, 1):
            print(f"  {i}. {f.name}")
            
        choice = input("Enter the number of the script to build: ").strip()
        try:
            idx = int(choice)
            if not (1 <= idx <= len(all_py)):
                raise ValueError
            script = all_py[idx - 1]
        except Exception:
            warn("Invalid choice – using the first script.")
            script = all_py[0]

    default_name = script.stem
    exe_name = input(f"EXE name (Enter = {default_name}): ").strip() or default_name
    exe_name = exe_name.strip(' .')
    if not exe_name:
        exe_name = default_name
    for ch in r'\/:*?"<>|':
        exe_name = exe_name.replace(ch, '_')
        
    used_modules = find_used_modules(base_dir, {'PIL', 'customtkinter', 'numpy'})
    options = ask_build_options(base_dir, used_modules)
    icon_path, is_temp = find_and_convert_icon(base_dir)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        f"--name={exe_name}"
    ]

    if not options.console:
        cmd.append("--noconsole")

    if icon_path:
        cmd.extend(["--icon", str(icon_path)])
        
    if options.admin:
        if is_windows:
            cmd.append("--uac-admin")
        else:
            warn("--uac-admin skipped (only available on Windows)")

    if options.include_numpy:
        cmd.append("--collect-all=numpy")
        info("NumPy will be bundled (--collect-all=numpy)")

    if options.include_pil:
        cmd.append("--collect-all=PIL")
        info("PIL will be bundled (--collect-all=PIL)")

    if 'customtkinter' in used_modules:
        cmd.append("--collect-all=customtkinter")
        info("customtkinter detected in project – added --collect-all") 

    cmd.append(str(script))
    
    dist_dir = base_dir / "dist"
    
    try:
        dist_dir.mkdir(exist_ok=True)
    except Exception as e:
        error(f"Cannot create dist directory: {e}")
        input("\nPress Enter to exit...")
        return 15

    info("Running PyInstaller...")
    success = False
    try:
        subprocess.run(cmd, check=True)
        success = True
    except subprocess.CalledProcessError as e:
        error(f"PyInstaller returned error code {e.returncode}")
        success = False

    cleanup(
        base_dir,
        exe_name,
        icon_path if is_temp else None,
        keep_spec=options.keep_spec if success else True
    )
    
    if not success:
        info("Build failed – .spec file kept for debugging.")

    elapsed = time.time() - start_time
    info(f"Build time: {elapsed:.1f} seconds")

    print()
    if success:
        exe_suffix = '.exe' if is_windows else ''
        exe_path = dist_dir / f"{exe_name}{exe_suffix}"
        if exe_path.exists():
            ok(f"Build successful! File: {exe_path}")
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            info(f"File size: {size_mb:.2f} MB")
        else:
            warn(f"Build reported success, but {exe_path} not found.")
    else:
        error("Build failed. Check the error messages above and examine the .spec file.")

    input("\nPress Enter to exit...")
    return 0 if success else 20
    

if __name__ == "__main__":
    sys.exit(main())
