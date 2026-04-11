"""
Phase 4 / PR1: launcher contract artifact validation.
"""
from __future__ import annotations

import json
from pathlib import Path


def test_backend_launcher_contract_has_required_shape() -> None:
    contract_path = Path("docs/backend-launcher-contract.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["version"] == 1
    assert contract["name"] == "backend-launcher-contract"

    assert set(contract["inputs"].keys()) >= {
        "mode",
        "backendRoot",
        "cwd",
        "host",
        "port",
    }
    assert contract["inputs"]["mode"]["enum"] == ["dev", "prod"]

    assert set(contract["outputs"].keys()) >= {"pid", "endpoint", "healthUrl", "stdioMode"}
    assert contract["outputs"]["stdioMode"]["enum"] == ["pipe", "inherit"]

    assert contract["health"]["path"] == "/health"
    assert contract["health"]["expectedJson"]["status"] == "healthy"
    assert contract["health"]["timeoutMs"] > 0
    assert contract["health"]["retryIntervalMs"] > 0

    assert set(contract["errors"].keys()) >= {"spawn_failure", "early_exit", "health_timeout"}


def test_startup_assumptions_checklist_tracks_current_main_process_coupling() -> None:
    checklist = Path("docs/startup-assumptions-checklist.md").read_text(encoding="utf-8")
    main_ts = Path("frontend/electron/main.ts").read_text(encoding="utf-8")

    assert "backend/venv/Scripts/python.exe" in checklist
    assert "backend.exe" in checklist
    assert "不等待 `/health` 就默认 backend 可用" in checklist
    assert "createBackendLauncherSpec" in main_ts
