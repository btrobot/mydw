"""
Phase 5 / PR4: cleanup/docs/frontend/backend truth alignment checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_system_openapi_describes_runtime_and_startup_boundaries(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()

    config_schema = spec["components"]["schemas"]["SystemConfigResponse"]
    assert "真实" in config_schema["description"]

    config_properties = config_schema["properties"]
    assert "唯一支持运行时修改" in config_properties["material_base_path"]["description"]
    assert "不支持运行时修改" in config_properties["auto_backup"]["description"]
    assert "启动期" in config_properties["log_level"]["description"]

    put_parameters = {
        item["name"]: item["description"]
        for item in spec["paths"]["/api/system/config"]["put"]["parameters"]
    }
    assert "唯一支持运行时修改" in put_parameters["material_base_path"]
    assert "不支持运行时修改" in put_parameters["auto_backup"]
    assert "启动期" in put_parameters["log_level"]


def test_settings_page_copy_matches_current_system_truth() -> None:
    settings_page = _read_repo_file("frontend/src/pages/Settings.tsx")

    assert "当前唯一支持的运行时设置项" in settings_page
    assert "自动备份" in settings_page
    assert "不支持运行时配置" in settings_page
    assert "最小真实备份产物" in settings_page
    assert ".env / backend/core/config.py" in settings_page
    assert "data/backups" in settings_page


def test_operational_notes_document_runtime_boundary_and_backup_scope() -> None:
    notes = _read_repo_file("docs/system-settings-operational-notes.md")

    assert "startup-env" in notes
    assert "runtime-config" in notes
    assert "material_base_path" in notes
    assert "auto_backup" in notes
    assert "log_level" in notes
    assert "data/system_config.json" in notes
    assert "data/backups" in notes
    assert "manifest.json" in notes
    assert "不支持运行时修改" in notes
