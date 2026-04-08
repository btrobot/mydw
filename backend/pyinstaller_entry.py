"""
PyInstaller entry point for backend.
Sets CWD to exe directory when frozen, then starts uvicorn programmatically.
"""
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    os.chdir(Path(sys.executable).parent)
    # Point patchright to globally installed browsers (%LOCALAPPDATA%/ms-playwright)
    if 'PLAYWRIGHT_BROWSERS_PATH' not in os.environ:
        global_browsers = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright'
        if global_browsers.exists():
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(global_browsers)

from main import app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
