from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "remote" / "remote-shared" / "scripts" / "compat-harness"
EXPORT_SCRIPT = HARNESS_ROOT / "export_phase1_openapi.py"
BUILD_SCRIPT = HARNESS_ROOT / "build_phase1_manifest.py"
VALIDATE_SCRIPT = HARNESS_ROOT / "validate_phase1_gate.py"
RUNTIME_OPENAPI_PATH = ROOT / "remote" / "remote-shared" / "openapi" / "remote-auth-runtime.json"
MANIFEST_PATH = ROOT / "remote" / "remote-shared" / "openapi" / "phase1-manifest.json"
RELEASE_DOC = ROOT / "remote" / "remote-shared" / "docs" / "phase1-release-gate.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "remote-phase1-release-gate.yml"


def run_python(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_phase1_release_gate_docs_and_workflow_exist() -> None:
    assert RELEASE_DOC.exists()
    text = RELEASE_DOC.read_text(encoding="utf-8")
    assert "staging-backed compatibility" in text
    assert "validate_phase1_gate.py" in text

    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert workflow["name"] == "remote-phase1-release-gate"
    assert "remote-backend-gate" in workflow["jobs"]
    assert "remote-admin-gate" in workflow["jobs"]
    install_step = next(
        step
        for step in workflow["jobs"]["remote-backend-gate"]["steps"]
        if step.get("name") == "Install backend + gate dependencies"
    )
    assert "httpx" in install_step["run"]


def test_phase1_runtime_openapi_can_be_exported() -> None:
    result = run_python(EXPORT_SCRIPT)
    assert result.returncode == 0, result.stderr
    assert RUNTIME_OPENAPI_PATH.exists()
    runtime_spec = json.loads(RUNTIME_OPENAPI_PATH.read_text(encoding="utf-8"))
    for path in ["/login", "/refresh", "/logout", "/me", "/admin/login", "/admin/session"]:
        assert path in runtime_spec["paths"]


def test_phase1_manifest_can_be_built() -> None:
    export = run_python(EXPORT_SCRIPT)
    assert export.returncode == 0, export.stderr
    result = run_python(BUILD_SCRIPT)
    assert result.returncode == 0, result.stderr
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["version"] == "phase1-v1"
    assert manifest["openapi_source"]["file"] == "remote-auth-v1.yaml"
    assert manifest["openapi_runtime"]["file"] == "remote-auth-runtime.json"


def test_phase1_gate_validation_script_passes() -> None:
    export = run_python(EXPORT_SCRIPT)
    assert export.returncode == 0, export.stderr
    build = run_python(BUILD_SCRIPT)
    assert build.returncode == 0, build.stderr
    validate = run_python(VALIDATE_SCRIPT)
    assert validate.returncode == 0, validate.stderr
    assert "PASS" in validate.stdout
