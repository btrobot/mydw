"""
Phase 4 / PR4: startup workflow consistency checks.
"""
from __future__ import annotations

import json
from pathlib import Path


def test_readme_and_startup_protocol_point_to_current_windows_flow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    protocol = Path("docs/guides/startup-protocol.md").read_text(encoding="utf-8")

    assert r".\dev.bat" in readme
    assert r".\scripts\start-backend.bat" in readme
    assert r".\scripts\start-frontend.bat" in readme
    assert r".\scripts\start-remote.bat" in readme
    assert "docs/guides/startup-protocol.md" in readme
    assert "Node.js 22+" in readme
    assert "Python 3.11+" in readme
    assert "http://127.0.0.1:8100" in readme
    assert "http://127.0.0.1:4173/index.html?apiBase=http://127.0.0.1:8100" in readme

    assert r".\dev.bat" in protocol
    assert r".\scripts\start-backend.bat" in protocol
    assert r".\scripts\start-frontend.bat" in protocol
    assert r".\scripts\start-remote.bat" in protocol
    assert "docs/specs/backend-launcher-contract.json" in protocol
    assert "Node.js 22+" in protocol
    assert "Python 3.11+" in protocol
    assert "127.0.0.1:8000" in protocol
    assert "127.0.0.1:8100" in protocol
    assert "127.0.0.1:4173" in protocol
    assert "/health" in protocol


def test_dev_and_backend_scripts_follow_launcher_protocol() -> None:
    dev_bat = Path("dev.bat").read_text(encoding="utf-8")
    backend_run = Path("backend/run.bat").read_text(encoding="utf-8")
    backend_setup = Path("backend/setup.bat").read_text(encoding="utf-8")

    assert r"call run.bat" in dev_bat
    assert r"frontend\electron\launchers\start-backend-dev.bat" in backend_run
    assert r".\run.bat" in backend_setup


def test_frontend_package_scripts_include_backend_dev_lane() -> None:
    package_json = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    scripts = package_json["scripts"]

    assert "backend:dev" in scripts
    assert "dev:electron" in scripts
    assert "npm run backend:dev" in scripts["dev:electron"]
