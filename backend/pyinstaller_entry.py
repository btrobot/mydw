"""
PyInstaller entry point for backend.
Sets CWD to exe directory when frozen, then starts uvicorn programmatically.
"""
import sys
import os
from pathlib import Path

# When frozen by PyInstaller, set CWD to exe directory
# so relative paths (data/, logs/) resolve correctly
if getattr(sys, 'frozen', False):
    os.chdir(Path(sys.executable).parent)

from main import app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
