"""
Phase 5 / PR1 baseline tests for system/settings truth.
"""
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_system_config_get_returns_current_placeholder_shape(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/system/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "material_base_path": "D:/系统/桌面/得物剪辑/待上传数据",
        "auto_backup": False,
        "log_level": "INFO",
    }


@pytest.mark.asyncio
async def test_system_config_put_rejects_unsupported_runtime_fields(
    client: AsyncClient,
) -> None:
    update = {
        "material_base_path": "E:/new-path",
        "auto_backup": True,
        "log_level": "DEBUG",
    }
    put_response = await client.put("/api/system/config", params=update)
    assert put_response.status_code == 400
    assert "不支持运行时修改" in put_response.json()["detail"]

    get_response = await client.get("/api/system/config")
    assert get_response.status_code == 200
    assert get_response.json() == {
        "material_base_path": "D:/系统/桌面/得物剪辑/待上传数据",
        "auto_backup": False,
        "log_level": "INFO",
    }


@pytest.mark.asyncio
async def test_system_backup_currently_returns_path_contract(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/system/backup", json={"include_logs": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    backup_file = Path(payload["backup_file"])
    assert backup_file.name == "manifest.json"
    assert backup_file.parent.parent.name == "backups"
    assert backup_file.suffix == ".json"


@pytest.mark.asyncio
async def test_material_stats_endpoint_is_read_only_shape(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/system/material-stats")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "videos",
        "copywritings",
        "covers",
        "audios",
        "topics",
        "products",
        "products_with_video",
        "coverage_rate",
    }
