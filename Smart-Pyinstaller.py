import io
import re
import shutil
import subprocess
import sys
import time

from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

USE_COLOR = sys.stdout.isatty()
GREEN = '\033[92m' if USE_COLOR else ''
YELLOW = '\033[93m' if USE_COLOR else ''
RED = '\033[91m' if USE_COLOR else ''
BLUE = '\033[94m' if USE_COLOR else ''
RESET = '\033[0m' if USE_COLOR else ''

def info(msg):
    print(f"{BLUE}[i]{RESET} {msg}")
def ok(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")
def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")
def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")

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
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]:
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
            sizes = [
                (256, 256), (128, 128), (64, 64),
                (48, 48), (32, 32), (16, 16)
            ]
            resample = getattr(Image, 'Resampling', Image).LANCZOS
            imgs = [square.resize(s, resample) for s in sizes]
            imgs[0].save(
                ico_path,
                format="ICO",
                sizes=[s for s in sizes],
                append_images=imgs[1:]
            )
        return ico_path, True
    except Exception as e:
        warn(f"Icon conversion failed: {e}")
        return None, False

def project_uses_customtkinter(base_dir):
    pattern = re.compile(
        r'^\s*(?:import\s+customtkinter|from\s+customtkinter\s+import)',
        re.MULTILINE
    )
    for py_file in base_dir.rglob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            if pattern.search(content):
                return True
        except Exception:
            pass
    return False

def project_uses_pil(base_dir):
    pattern = re.compile(
        r'^\s*(?:import\s+PIL|from\s+PIL\s+import)',
        re.MULTILINE
    )
    for py_file in base_dir.rglob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            if pattern.search(content):
                return True
        except Exception:
            pass
    return False

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
                "(it may be locked by antivirus or system): {e}"
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
            script = all_py[int(choice) - 1]
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

    console = input("Show console window? (y/N, Enter: N): ").strip().lower() == 'y'
    admin = input("Request administrator privileges on launch? (y/N, Enter: N): ").strip().lower() == 'y'
    icon_path, is_temp = find_and_convert_icon(base_dir)
    keep_spec = input("Keep .spec file after build for later use? (y/N, Enter: N): ").strip().lower() == 'y'
    include_numpy = input("Include NumPy explicitly? (y/N, Enter: N): ").strip().lower() == 'y'

    uses_pil_in_code = project_uses_pil(base_dir)
    
    if uses_pil_in_code:
        warn("PIL (Pillow) imports detected in your project source code.")
        include_pil = input("Include PIL in the build? (y/N, Enter: N): ").strip().lower() == 'y'
    else:
        include_pil = input("Include PIL (Pillow) in the build? (y/N, Enter: N): ").strip().lower() == 'y'

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        f"--name={exe_name}"
    ]

    if not console:
        cmd.append("--noconsole")

    if icon_path:
        cmd.extend(["--icon", str(icon_path)])
    if admin:
        if is_windows:
            cmd.append("--uac-admin")
        else:
            warn("--uac-admin skipped (only available on Windows)")

    if include_numpy:
        cmd.append("--collect-all=numpy")
        info("NumPy will be bundled (--collect-all=numpy)")
    else:
        cmd.append("--exclude-module=numpy")
        warn("NumPy will be EXCLUDED. If your code actually needs it, the build will fail.")

    if include_pil:
        cmd.append("--collect-all=PIL")
        info("PIL will be bundled (--collect-all=PIL)")
    else:
        cmd.append("--exclude-module=PIL")
        warn("PIL will be EXCLUDED. If your code actually needs it, the build will fail.")

    if project_uses_customtkinter(base_dir):
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
        keep_spec=keep_spec if success else True
    )

    if not success:
        info("Build failed – .spec file kept for debugging.")

    elapsed = time.time() - start_time
    info(f"Build time: {elapsed:.1f} seconds")

    print()
    if success:
        exe_suffix = '.exe' if is_windows else ''
        exe_path = dist_dir / f"{exe_name}{exe_suffix}"
        ok(f"Build successful! File: {exe_path}")
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        info(f"File size: {size_mb:.2f} MB")
    else:
        error("Build failed. Check the error messages above and examine the .spec file.")

    input("\nPress Enter to exit...")
    return 0 if success else 20

if __name__ == "__main__":
    sys.exit(main())
