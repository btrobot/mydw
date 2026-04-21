"""
PR-B: generated artifact governance contract checks.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
import textwrap
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict:
    return json.loads(_read(relative_path))


def test_generated_artifact_policy_lists_boundary_matrix_and_rules() -> None:
    policy = _read("docs/governance/policies/generated-artifact-policy.md")

    assert "source of truth" in policy
    assert "generated artifact" in policy
    assert "frontend/openapi.local.json" in policy
    assert "frontend/src/api/" in policy
    assert "frontend/electron/main.ts" in policy
    assert "frontend/electron/main.js" in policy
    assert "frontend/electron/main.js.map" in policy
    assert "frontend/electron/preload.ts" in policy
    assert "frontend/electron/preload.js" in policy
    assert "frontend/electron/backendLauncher.ts" in policy
    assert "frontend/electron/backendLauncher.js" in policy
    assert "tracked generated artifact" in policy
    assert "must be regenerated locally" in policy or "必须通过命令重建" in policy


def test_openapi_workflow_points_to_standard_regenerate_and_check_entrypoints() -> None:
    workflow = _read("docs/guides/openapi-generation-workflow.md")

    assert "docs/governance/policies/generated-artifact-policy.md" in workflow
    assert "frontend/openapi.local.json" in workflow
    assert "frontend/src/api/" in workflow
    assert "npm run generated:regenerate" in workflow
    assert "npm run generated:check" in workflow


def test_frontend_package_exposes_generated_regenerate_and_check_scripts() -> None:
    package = _read_json("frontend/package.json")
    scripts = package["scripts"]

    assert "generated:regenerate" in scripts
    assert "api:generate" in scripts["generated:regenerate"]
    assert "tsc -p electron/tsconfig.json" in scripts["generated:regenerate"]

    assert "generated:check" in scripts
    assert "node scripts/check-generated-artifacts.mjs" in scripts["generated:check"]


def test_generated_check_script_covers_tracked_generated_surfaces() -> None:
    check_script = _read("frontend/scripts/check-generated-artifacts.mjs")

    assert "generated:regenerate" in check_script
    assert "openapi.local.json" in check_script
    assert "src/api" in check_script
    assert "electron/main.js" in check_script
    assert "electron/main.js.map" in check_script
    assert "electron/preload.js" in check_script
    assert "electron/preload.js.map" in check_script
    assert "electron/backendLauncher.js" in check_script
    assert "electron/backendLauncher.js.map" in check_script
    assert "'status'" in check_script or '"status"' in check_script


def test_generated_check_fails_when_regenerate_changes_already_dirty_tracked_file() -> None:
    script_path = REPO_ROOT / "frontend/scripts/check-generated-artifacts.mjs"

    with TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=repo_root, check=True)

        (repo_root / "package.json").write_text(
            json.dumps({"name": "tmp-generated-check", "version": "1.0.0", "scripts": {"generated:regenerate": "node regen.mjs"}}),
            encoding="utf-8",
        )
        (repo_root / "regen.mjs").write_text(
            textwrap.dedent(
                """
                import { writeFileSync } from 'node:fs'
                writeFileSync('openapi.local.json', JSON.stringify({ version: 2 }) + '\\n')
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (repo_root / "openapi.local.json").write_text('{"version":1}\n', encoding="utf-8")
        (repo_root / "src").mkdir()
        (repo_root / "src/api").mkdir()
        (repo_root / "src/api/sdk.gen.ts").write_text("// initial\n", encoding="utf-8")
        (repo_root / "electron").mkdir()
        (repo_root / "electron/main.js").write_text("// main\n", encoding="utf-8")
        (repo_root / "electron/main.js.map").write_text("{}\n", encoding="utf-8")
        (repo_root / "electron/preload.js").write_text("// preload\n", encoding="utf-8")
        (repo_root / "electron/preload.js.map").write_text("{}\n", encoding="utf-8")
        (repo_root / "electron/backendLauncher.js").write_text("// launcher\n", encoding="utf-8")
        (repo_root / "electron/backendLauncher.js.map").write_text("{}\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

        (repo_root / "openapi.local.json").write_text('{"version":"dirty-before"}\n', encoding="utf-8")

        result = subprocess.run(
            ["node", str(script_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Generated artifact drift changed after regeneration." in result.stderr
        assert "Content drift:" in result.stderr
        assert "openapi.local.json" in result.stderr


def test_version_inventory_calls_out_generated_noncanonical_boundaries() -> None:
    inventory = _read("docs/governance/inventory/epic-7-version-inventory.md")

    assert "frontend/electron/main.js" in inventory
    assert "generated JS mirror" in inventory or "generated mirror" in inventory
    assert "frontend/openapi.local.json" in inventory
    assert "generated snapshot" in inventory or "generated artifact" in inventory
