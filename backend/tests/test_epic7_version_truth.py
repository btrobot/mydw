"""
Epic 7 / PR3: version and release metadata consistency checks.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    assert match, f"pattern not found: {pattern}"
    return match.group(1)


def test_user_visible_version_surfaces_match_app_version() -> None:
    backend_config = _read("backend/core/config.py")
    canonical = _extract(r'APP_VERSION:\s*str\s*=\s*"([^"]+)"', backend_config)

    readme = _read("README.md")
    backend_main = _read("backend/main.py")
    frontend_pkg = _read("frontend/package.json")
    electron_main_ts = _read("frontend/electron/main.ts")
    electron_main_js = _read("frontend/electron/main.js")
    cli_pkg = _read("frontend/scripts/cli/package.json")
    cli_src = _read("frontend/scripts/cli/src/index.ts")
    openapi_local = _read("frontend/openapi.local.json")

    assert f"**版本**: {canonical}" in readme
    assert "version=settings.APP_VERSION" in backend_main
    assert '"version": settings.APP_VERSION' in backend_main
    assert f'"version": "{canonical}"' in frontend_pkg
    assert "app.getVersion()" in electron_main_ts
    assert "getVersion()" in electron_main_js
    assert f'"version": "{canonical}"' in cli_pkg
    assert f"const VERSION = '{canonical}'" in cli_src
    assert f'"version": "{canonical}"' in openapi_local


def test_version_inventory_documents_canonical_source_and_exclusions() -> None:
    inventory = _read("docs/epic-7-version-inventory.md")

    assert "backend/core/config.py" in inventory
    assert "APP_VERSION" in inventory
    assert "canonical version source" in inventory or "canonical source" in inventory
    assert "README.md" in inventory
    assert "frontend/package.json" in inventory
    assert "frontend/electron/main.ts" in inventory
    assert "frontend/scripts/cli/src/index.ts" in inventory
    assert "frontend/openapi.local.json" in inventory
    assert "package-lock" in inventory or "lockfile" in inventory
