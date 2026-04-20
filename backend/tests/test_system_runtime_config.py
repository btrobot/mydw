"""
Phase 5 / PR2: truthful runtime config tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import services.system_config_service as system_config_service
from core.config import settings


@pytest.fixture()
def runtime_config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "system_config.json"
    monkeypatch.setattr(system_config_service, "RUNTIME_CONFIG_PATH", path)
    return path


@pytest.mark.asyncio
async def test_system_config_falls_back_to_startup_env_when_runtime_file_missing(
    client,
    runtime_config_file: Path,
) -> None:
    response = await client.get("/api/system/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["material_base_path"] == settings.MATERIAL_BASE_PATH
    assert payload["creative_flow_mode"] == "creative_first"
    assert payload["creative_flow_shadow_compare"] is False
    assert payload["log_level"] == settings.LOG_LEVEL
    assert payload["auto_backup"] is False
    assert not runtime_config_file.exists()


@pytest.mark.asyncio
async def test_system_config_put_persists_supported_runtime_fields(
    client,
    runtime_config_file: Path,
) -> None:
    response = await client.put(
        "/api/system/config",
        params={
            "material_base_path": "E:/runtime-path",
            "creative_flow_mode": "dual",
            "creative_flow_shadow_compare": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["material_base_path"] == "E:/runtime-path"
    assert payload["creative_flow_mode"] == "dual"
    assert payload["creative_flow_shadow_compare"] is True
    assert payload["log_level"] == settings.LOG_LEVEL
    assert payload["auto_backup"] is False

    persisted = json.loads(runtime_config_file.read_text(encoding="utf-8"))
    assert persisted["material_base_path"] == "E:/runtime-path"
    assert persisted["creative_flow_mode"] == "dual"
    assert persisted["creative_flow_shadow_compare"] is True

    get_again = await client.get("/api/system/config")
    assert get_again.status_code == 200
    assert get_again.json()["material_base_path"] == "E:/runtime-path"
    assert get_again.json()["creative_flow_mode"] == "dual"
    assert get_again.json()["creative_flow_shadow_compare"] is True


@pytest.mark.asyncio
async def test_system_config_rejects_unsupported_runtime_fields(
    client,
    runtime_config_file: Path,
) -> None:
    response = await client.put(
        "/api/system/config",
        params={
            "material_base_path": "E:/runtime-path",
            "auto_backup": "true",
            "log_level": "DEBUG",
        },
    )

    assert response.status_code == 400
    assert "不支持运行时修改" in response.json()["detail"]
    assert not runtime_config_file.exists()


@pytest.mark.asyncio
async def test_system_config_rejects_invalid_creative_flow_mode(
    client,
    runtime_config_file: Path,
) -> None:
    response = await client.put(
        "/api/system/config",
        params={"creative_flow_mode": "unknown-mode"},
    )

    assert response.status_code == 400
    assert "creative_flow_mode 非法" in response.json()["detail"]
    assert not runtime_config_file.exists()
