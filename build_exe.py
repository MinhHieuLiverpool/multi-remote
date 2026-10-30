"""
Build Script for Multi Remote Desktop Manager
Compiles the project into a standalone Windows .exe file.

Usage:
    python build_exe.py
"""
import os
import sys
import shutil
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
SPEC_FILE = os.path.join(PROJECT_DIR, "MultiRemoteDesktop.spec")
EXE_NAME = "MultiRemoteDesktop"


def print_step(msg):
    print("\n" + "=" * 65)
    print(f"  {msg}")
    print("=" * 65)


def check_prerequisites():
    print_step("1. Checking Prerequisites")
    print(f"[OK] Python version: {sys.version.split()[0]}")

    try:
        import PyInstaller
        print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed successfully.")


def run_build():
    print_step("2. Compiling Executable (.exe)")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        SPEC_FILE
    ]

    print("Running command:", " ".join(cmd))
    print("\nBuilding... Please wait (takes ~30-60s)...")
    res = subprocess.run(cmd, cwd=PROJECT_DIR)
    if res.returncode != 0:
        print(f"\n[ERROR] Build failed with code {res.returncode}")
        sys.exit(res.returncode)


def finalize_build():
    print_step("3. Finalizing Build & Distributing Presets")

    exe_path = os.path.join(DIST_DIR, f"{EXE_NAME}.exe")
    if not os.path.exists(exe_path):
        print(f"[ERROR] Executable not found at {exe_path}")
        sys.exit(1)

    file_size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"[SUCCESS] Standalone Executable built: {exe_path}")
    print(f"[INFO] Size: {file_size_mb:.2f} MB")

    # Copy connections.json so the .exe has initial servers ready
    src_json = os.path.join(PROJECT_DIR, "connections.json")
    dst_json = os.path.join(DIST_DIR, "connections.json")
    if os.path.exists(src_json):
        shutil.copy2(src_json, dst_json)
        print(f"[COPIED] connections.json -> dist/ (ready to use)")

    print_step("Build Completed Successfully!")
    print(f"File exe da san sang tai:")
    print(f"--> {exe_path}\n")


if __name__ == "__main__":
    try:
        check_prerequisites()
        run_build()
        finalize_build()
    except KeyboardInterrupt:
        print("\n[CANCELLED] Cancelled by user.")
        sys.exit(1)
