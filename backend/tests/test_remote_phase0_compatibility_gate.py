from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "remote" / "remote-shared" / "scripts" / "compat-harness"
BUILD_SCRIPT = HARNESS_ROOT / "build_phase0_manifest.py"
VALIDATE_SCRIPT = HARNESS_ROOT / "validate_phase0_gate.py"
MANIFEST_PATH = ROOT / "remote" / "remote-shared" / "openapi" / "phase0-manifest.json"


def run_python(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_phase0_manifest_can_be_built() -> None:
    result = run_python(BUILD_SCRIPT)
    assert result.returncode == 0, result.stderr
    assert MANIFEST_PATH.exists()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["version"] == "phase0-v1"
    assert "openapi" in manifest
    assert manifest["fixtures"]


def test_phase0_gate_validation_script_passes() -> None:
    build = run_python(BUILD_SCRIPT)
    assert build.returncode == 0, build.stderr

    validate = run_python(VALIDATE_SCRIPT)
    assert validate.returncode == 0, validate.stderr
    assert "PASS" in validate.stdout
