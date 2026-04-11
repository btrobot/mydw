"""
Phase 4 / PR2: launcher layer regression checks.
"""
from pathlib import Path


def test_electron_main_no_longer_hardcodes_backend_environment_paths() -> None:
    main_ts = Path("frontend/electron/main.ts").read_text(encoding="utf-8")

    assert "backend/venv/Scripts/python.exe" not in main_ts
    assert "backend.exe" not in main_ts
    assert "uvicorn main:app" not in main_ts
    assert "createBackendLauncherSpec" in main_ts
    assert "waitForBackendHealth" in main_ts


def test_launcher_scripts_exist_for_dev_and_prod_modes() -> None:
    launchers = Path("frontend/electron/launchers")
    expected = {
        "start-backend-dev.bat",
        "start-backend-dev.sh",
        "start-backend-prod.bat",
        "start-backend-prod.sh",
    }

    assert expected.issubset({path.name for path in launchers.iterdir() if path.is_file()})


def test_backend_launcher_spec_keeps_canonical_mode_structure() -> None:
    launcher_helper = Path("frontend/electron/backendLauncher.ts").read_text(encoding="utf-8")

    assert "mode" not in launcher_helper or "dev" in launcher_helper
    assert "healthUrl" in launcher_helper
    assert "BACKEND_ROOT" in launcher_helper
