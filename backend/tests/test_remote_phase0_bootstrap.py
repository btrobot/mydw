from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REMOTE_ROOT = ROOT / "remote"


def test_remote_workspace_directories_exist() -> None:
    expected = [
        REMOTE_ROOT,
        REMOTE_ROOT / "remote-backend",
        REMOTE_ROOT / "remote-admin",
        REMOTE_ROOT / "remote-shared",
        REMOTE_ROOT / "remote-shared" / "openapi",
        REMOTE_ROOT / "remote-shared" / "docs",
        REMOTE_ROOT / "remote-shared" / "scripts",
    ]
    for path in expected:
        assert path.exists(), f"missing expected path: {path}"


def test_remote_backend_pyproject_and_placeholder_app_are_valid() -> None:
    pyproject = tomllib.loads(
        (REMOTE_ROOT / "remote-backend" / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert pyproject["project"]["name"] == "remote-backend"
    assert pyproject["project"]["requires-python"] == ">=3.11"

    import sys

    sys.path.insert(0, str(REMOTE_ROOT / "remote-backend"))
    from app.main import create_app  # noqa: WPS433

    app = create_app()
    assert app.title == "Remote Auth API"
    assert any(route.path == "/login" for route in app.routes)


def test_remote_admin_package_json_and_scripts_are_valid() -> None:
    package = json.loads(
        (REMOTE_ROOT / "remote-admin" / "package.json").read_text(encoding="utf-8")
    )
    assert package["name"] == "remote-admin"
    for script in ["dev", "typecheck", "build", "lint"]:
        assert script in package["scripts"]


def test_remote_phase0_workflow_yaml_parses() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "remote-phase0-bootstrap.yml").read_text(
            encoding="utf-8"
        )
    )
    assert workflow["name"] == "remote-phase0-bootstrap"
    assert "backend-skeleton" in workflow["jobs"]
    assert "admin-skeleton" in workflow["jobs"]
