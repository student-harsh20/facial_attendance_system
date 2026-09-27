"""
Launcher script for Face Recognition Attendance System.
Run:
    python run.py
"""
import os
import sys
import subprocess
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Auto-switch to project virtual environment if run from system Python
venv_win = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
venv_posix = PROJECT_ROOT / "venv" / "bin" / "python"
venv_python = venv_win if venv_win.exists() else (venv_posix if venv_posix.exists() else None)

if venv_python:
    try:
        is_current_venv = Path(sys.executable).resolve() == venv_python.resolve()
    except Exception:
        is_current_venv = False
    if not is_current_venv:
        cmd = [str(venv_python)] + sys.argv
        sys.exit(subprocess.call(cmd))

# Reconfigure stdout/stderr for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import webbrowser
import threading
import time
import uvicorn

from backend.config import settings


def open_browser(url: str):
    time.sleep(1.5)
    try:
        print(f"\n[Browser] Opening interface at {url}...")
        webbrowser.open(url)
    except Exception as e:
        print(f"[Browser] Could not auto-open browser: {e}")


def main():
    print("=" * 65)
    print("       *** FACE RECOGNITION ATTENDANCE SYSTEM ***")
    print("                College Minor Project")
    print("=" * 65)
    print(f"Backend Server : http://{settings.HOST}:{settings.PORT}")
    print(f"API Docs (Swagger): http://localhost:{settings.PORT}/docs")
    print(f"Recognition Cooldown Buffer: {settings.RECOGNITION_COOLDOWN_SECONDS} seconds")
    print(f"Database       : {settings.DATABASE_URL}")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.\n")

    # Auto-open browser on desktop if not running in a headless cloud container
    is_headless = (
        os.environ.get("HEADLESS", "").lower() in ("1", "true")
        or os.environ.get("RENDER") is not None
        or os.environ.get("RAILWAY_ENVIRONMENT") is not None
        or (sys.platform != "win32" and not os.environ.get("DISPLAY"))
    )
    if not is_headless:
        local_url = f"http://localhost:{settings.PORT}"
        threading.Thread(target=open_browser, args=(local_url,), daemon=True).start()

    # Launch Uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
