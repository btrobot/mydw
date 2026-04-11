"""
Phase 3 / PR1: high-value OpenAPI contract parity checks.
"""
import pytest
from httpx import AsyncClient


def _find_parameter(parameters: list[dict], name: str) -> dict:
    return next(param for param in parameters if param["name"] == name)


@pytest.mark.asyncio
async def test_account_list_openapi_includes_status_tag_and_search_filters(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    path = response.json()["paths"]["/api/accounts/"]["get"]
    parameters = path["parameters"]

    assert _find_parameter(parameters, "status")["schema"]["type"] == "string"
    assert _find_parameter(parameters, "tag")["schema"]["anyOf"][0]["type"] == "string"
    assert _find_parameter(parameters, "search")["schema"]["anyOf"][0]["type"] == "string"


@pytest.mark.asyncio
async def test_preview_and_system_paths_have_explicit_response_schemas(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]

    preview_open = paths["/api/accounts/{account_id}/preview"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    preview_close = paths["/api/accounts/{account_id}/preview/close"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    system_config = paths["/api/system/config"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    system_update = paths["/api/system/config"]["put"]["responses"]["200"]["content"]["application/json"]["schema"]
    backup = paths["/api/system/backup"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    material_stats = paths["/api/system/material-stats"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    assert preview_open["$ref"].endswith("/PreviewActionResponse")
    assert preview_close["$ref"].endswith("/PreviewActionResponse")
    assert system_config["$ref"].endswith("/SystemConfigResponse")
    assert system_update["$ref"].endswith("/SystemConfigUpdateResponse")
    assert backup["$ref"].endswith("/BackupResponse")
    assert material_stats["$ref"].endswith("/MaterialStatsResponse")


@pytest.mark.asyncio
async def test_task_response_openapi_remains_collection_based(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    task_response = response.json()["components"]["schemas"]["TaskResponse"]["properties"]
    assert "video_ids" in task_response
    assert "copywriting_ids" in task_response
    assert "cover_ids" in task_response
    assert "audio_ids" in task_response
    assert "topic_ids" in task_response
