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


@pytest.mark.asyncio
async def test_task_response_openapi_includes_phase_a_creative_fields(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    task_response = response.json()["components"]["schemas"]["TaskResponse"]["properties"]

    assert task_response["creative_item_id"]["anyOf"][0]["type"] == "integer"
    assert task_response["creative_version_id"]["anyOf"][0]["type"] == "integer"
    assert task_response["task_kind"]["anyOf"][0]["$ref"].endswith("/TaskKind")

    task_kind = response.json()["components"]["schemas"]["TaskKind"]
    assert task_kind["type"] == "string"
    assert task_kind["enum"] == ["composition", "publish"]


@pytest.mark.asyncio
async def test_task_create_and_update_openapi_do_not_expose_task_kind(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()["components"]["schemas"]
    assert "task_kind" not in spec["TaskCreateRequest"]["properties"]
    assert "task_kind" not in spec["TaskUpdate"]["properties"]


@pytest.mark.asyncio
async def test_creative_openapi_exposes_phase_a_workbench_and_detail_contracts(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]
    schemas = spec["components"]["schemas"]

    assert paths["/api/creatives"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeWorkbenchListResponse")
    assert paths["/api/creatives/{creative_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeDetailResponse")
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["package_record_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeDetailResponse"]["properties"]["linked_task_ids"]["type"] == "array"
    assert schemas["CreativeDetailResponse"]["properties"]["versions"]["type"] == "array"
    assert schemas["CreativeDetailResponse"]["properties"]["review_summary"]["anyOf"][0]["$ref"].endswith("/CreativeReviewSummaryResponse")


@pytest.mark.asyncio
async def test_creative_review_openapi_exposes_phase_b_review_contracts(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]
    schemas = spec["components"]["schemas"]

    assert paths["/api/creative-reviews/{creative_id}/approve"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeApproveRequest")
    assert paths["/api/creative-reviews/{creative_id}/rework"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeReworkRequest")
    assert paths["/api/creative-reviews/{creative_id}/reject"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeRejectRequest")
    assert paths["/api/creative-reviews/{creative_id}/approve"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeReviewActionResponse")
    assert schemas["CheckRecordResponse"]["properties"]["conclusion"]["$ref"].endswith("/CreativeReviewConclusion")
    assert "WAITING_REVIEW" in schemas["CreativeStatus"]["enum"]
    assert "REWORK_REQUIRED" in schemas["CreativeReviewConclusion"]["enum"]


@pytest.mark.asyncio
async def test_creative_publish_pool_openapi_exposes_phase_c_pool_contracts(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]
    schemas = spec["components"]["schemas"]

    assert paths["/api/creative-publish-pool"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/PublishPoolListResponse")
    assert paths["/api/creative-publish-pool/{pool_item_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/PublishPoolItemResponse")
    status_param = _find_parameter(paths["/api/creative-publish-pool"]["get"]["parameters"], "status")
    assert status_param["schema"]["anyOf"][0]["$ref"].endswith("/PublishPoolStatus")
    assert schemas["PublishPoolItemResponse"]["properties"]["creative_status"]["anyOf"][0]["$ref"].endswith("/CreativeStatus")
    assert schemas["PublishPoolStatus"]["enum"] == ["active", "invalidated"]


@pytest.mark.asyncio
async def test_scheduler_cutover_openapi_exposes_phase_c_runtime_controls(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    schedule_config = spec["components"]["schemas"]["ScheduleConfigResponse"]["properties"]
    publish_status = spec["components"]["schemas"]["PublishStatusResponse"]["properties"]
    publish_scheduler_mode = spec["components"]["schemas"]["PublishSchedulerMode"]

    assert schedule_config["publish_scheduler_mode"]["$ref"].endswith("/PublishSchedulerMode")
    assert schedule_config["publish_pool_kill_switch"]["type"] == "boolean"
    assert schedule_config["publish_pool_shadow_read"]["type"] == "boolean"
    assert publish_status["scheduler_mode"]["$ref"].endswith("/PublishSchedulerMode")
    assert publish_status["effective_scheduler_mode"]["$ref"].endswith("/PublishSchedulerMode")
    assert publish_status["publish_pool_kill_switch"]["type"] == "boolean"
    assert publish_status["publish_pool_shadow_read"]["type"] == "boolean"
    assert publish_scheduler_mode["enum"] == ["task", "pool"]


@pytest.mark.asyncio
async def test_product_create_openapi_requires_name_and_share_text(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    product_create = spec["components"]["schemas"]["ProductCreate"]
    properties = product_create["properties"]

    assert set(product_create["required"]) == {"name", "share_text"}
    assert properties["name"]["maxLength"] == 256
    assert properties["share_text"]["maxLength"] == 2048

    request_body_schema = (
        spec["paths"]["/api/products"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    )
    assert request_body_schema["$ref"].endswith("/ProductCreate")
