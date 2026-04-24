"""
Phase 3 / PR1: high-value OpenAPI contract parity checks.
"""
import json
from pathlib import Path

import pytest
from httpx import AsyncClient


def _find_parameter(parameters: list[dict], name: str) -> dict:
    return next(param for param in parameters if param["name"] == name)


def _load_exported_openapi() -> dict:
    return json.loads(
        Path("frontend/openapi.local.json").read_text(encoding="utf-8")
    )


def _schema_property_names(spec: dict, schema_name: str) -> set[str]:
    return set(spec["components"]["schemas"][schema_name].get("properties", {}).keys())


def _schema_refs(spec: dict, schema_name: str, property_names: tuple[str, ...]) -> dict[str, str]:
    properties = spec["components"]["schemas"][schema_name]["properties"]
    refs: dict[str, str] = {}
    for property_name in property_names:
        property_schema = properties[property_name]
        if "$ref" in property_schema:
            refs[property_name] = property_schema["$ref"]
        else:
            refs[property_name] = property_schema["anyOf"][0]["$ref"]
    return refs


def _schema_property(spec: dict, schema_name: str, property_name: str) -> dict:
    return spec["components"]["schemas"][schema_name]["properties"][property_name]


PHASE1_CREATIVE_SCHEMA_NAMES = (
    "CreativeCreateRequest",
    "CreativeUpdateRequest",
    "CreativeDetailResponse",
    "CreativeWorkbenchItemResponse",
    "CreativeWorkbenchListResponse",
    "CreativeWorkbenchSummaryResponse",
    "CreativeInputItemResponse",
    "CreativeInputItemWrite",
    "CreativeInputOrchestrationResponse",
    "CreativeInputMaterialCountsResponse",
)

PHASE1_CREATIVE_ENUM_SCHEMA_NAMES = (
    "CreativeInputMaterialType",
    "CreativeEligibilityStatus",
    "CreativeWorkbenchPoolState",
    "CreativeWorkbenchSort",
)

PHASE1_CREATIVE_DETAIL_REF_FIELDS = (
    "input_orchestration",
    "eligibility_status",
    "latest_task_summary",
)

PHASE2_LEGACY_CREATIVE_WRITE_FIELDS = (
    "video_ids",
    "copywriting_ids",
    "cover_ids",
    "audio_ids",
    "topic_ids",
)

SLICE1_CURRENT_TRUTH_FIELDS = (
    "current_product_name",
    "product_name_mode",
    "current_cover_asset_type",
    "current_cover_asset_id",
    "cover_mode",
    "current_copywriting_id",
    "current_copywriting_text",
    "copywriting_mode",
)


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
async def test_creative_openapi_exposes_phase4_workbench_and_detail_contracts(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]
    schemas = spec["components"]["schemas"]

    assert paths["/api/creatives"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeWorkbenchListResponse")
    list_parameters = paths["/api/creatives"]["get"]["parameters"]
    assert _find_parameter(list_parameters, "keyword")["schema"]["anyOf"][0]["type"] == "string"
    assert _find_parameter(list_parameters, "status")["schema"]["anyOf"][0]["$ref"].endswith("/CreativeStatus")
    assert _find_parameter(list_parameters, "pool_state")["schema"]["anyOf"][0]["$ref"].endswith("/CreativeWorkbenchPoolState")
    assert _find_parameter(list_parameters, "sort")["schema"]["$ref"].endswith("/CreativeWorkbenchSort")
    assert _find_parameter(list_parameters, "recent_failures_only")["schema"]["type"] == "boolean"
    assert paths["/api/creatives"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeCreateRequest")
    assert paths["/api/creatives"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeDetailResponse")
    assert paths["/api/creatives/{creative_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeDetailResponse")
    assert paths["/api/creatives/{creative_id}"]["patch"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeUpdateRequest")
    assert paths["/api/creatives/{creative_id}"]["patch"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CreativeDetailResponse")
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["package_record_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["package_record"]["anyOf"][0]["$ref"].endswith("/PackageRecordResponse")
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["final_product_name"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["final_copywriting_text"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeCurrentVersionResponse"]["properties"]["actual_duration_seconds"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeCreateRequest"]["properties"]["subject_product_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeCreateRequest"]["properties"]["main_copywriting_text"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeCreateRequest"]["properties"]["target_duration_seconds"]["anyOf"][0]["type"] == "integer"
    for field_name in SLICE1_CURRENT_TRUTH_FIELDS:
        assert field_name in schemas["CreativeCreateRequest"]["properties"]
        assert field_name in schemas["CreativeUpdateRequest"]["properties"]
        assert field_name in schemas["CreativeDetailResponse"]["properties"]
        assert field_name in schemas["CreativeWorkbenchItemResponse"]["properties"]
    assert schemas["CreativeCreateRequest"]["properties"]["input_items"]["type"] == "array"
    assert schemas["CreativeUpdateRequest"]["properties"]["input_items"]["anyOf"][0]["type"] == "array"
    assert "authoritative writes only accept video/audio" in schemas["CreativeCreateRequest"]["properties"]["input_items"]["description"]
    assert "authoritative writes only accept video/audio" in schemas["CreativeUpdateRequest"]["properties"]["input_items"]["description"]
    assert schemas["CreativeCreateRequest"]["properties"]["product_name_mode"]["anyOf"][0]["$ref"].endswith("/CreativeProductNameMode")
    assert schemas["CreativeCreateRequest"]["properties"]["current_cover_asset_type"]["anyOf"][0]["$ref"].endswith("/CreativeCurrentCoverAssetType")
    assert schemas["CreativeCreateRequest"]["properties"]["cover_mode"]["anyOf"][0]["$ref"].endswith("/CreativeCoverMode")
    assert schemas["CreativeCreateRequest"]["properties"]["copywriting_mode"]["anyOf"][0]["$ref"].endswith("/CreativeCopywritingMode")
    for field_name in PHASE2_LEGACY_CREATIVE_WRITE_FIELDS:
        assert schemas["CreativeCreateRequest"]["properties"][field_name]["deprecated"] is True
        assert schemas["CreativeUpdateRequest"]["properties"][field_name]["deprecated"] is True
        assert "compatibility-only projection" in schemas["CreativeCreateRequest"]["properties"][field_name]["description"]
        assert "compatibility-only projection" in schemas["CreativeUpdateRequest"]["properties"][field_name]["description"]
    write_material_type_ref = schemas["CreativeInputItemWrite"]["properties"]["material_type"]["$ref"]
    assert write_material_type_ref.endswith("/CreativeSelectedMediaWriteMaterialType")
    assert schemas["CreativeSelectedMediaWriteMaterialType"]["enum"] == ["video", "audio"]
    assert schemas["CreativeInputItemResponse"]["properties"]["material_type"]["$ref"].endswith("/CreativeInputMaterialType")
    assert schemas["CreativeInputItemResponse"]["properties"]["material_id"]["type"] == "integer"
    assert "CreativeInputSnapshotResponse" not in schemas
    assert schemas["CreativeInputOrchestrationResponse"]["properties"]["orchestration_hash"]["type"] == "string"
    assert schemas["CreativeInputOrchestrationResponse"]["properties"]["item_count"]["type"] == "integer"
    assert schemas["CreativeInputOrchestrationResponse"]["properties"]["enabled_item_count"]["type"] == "integer"
    assert schemas["CreativeInputOrchestrationResponse"]["properties"]["material_counts"]["$ref"].endswith("/CreativeInputMaterialCountsResponse")
    assert schemas["CreativeInputOrchestrationResponse"]["properties"]["enabled_material_counts"]["$ref"].endswith("/CreativeInputMaterialCountsResponse")
    assert schemas["CreativeDetailResponse"]["properties"]["linked_task_ids"]["type"] == "array"
    assert schemas["CreativeDetailResponse"]["properties"]["versions"]["type"] == "array"
    assert schemas["CreativeDetailResponse"]["properties"]["review_summary"]["anyOf"][0]["$ref"].endswith("/CreativeReviewSummaryResponse")
    assert schemas["CreativeDetailResponse"]["properties"]["subject_product_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeDetailResponse"]["properties"]["main_copywriting_text"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeDetailResponse"]["properties"]["target_duration_seconds"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeDetailResponse"]["properties"]["input_items"]["type"] == "array"
    assert "full-carrier compatibility readback" in schemas["CreativeDetailResponse"]["properties"]["input_items"]["description"]
    assert schemas["CreativeDetailResponse"]["properties"]["input_orchestration"]["$ref"].endswith("/CreativeInputOrchestrationResponse")
    assert "input_snapshot" not in schemas["CreativeDetailResponse"]["properties"]
    assert schemas["CreativeDetailResponse"]["properties"]["eligibility_status"]["$ref"].endswith("/CreativeEligibilityStatus")
    assert schemas["CreativeDetailResponse"]["properties"]["latest_task_summary"]["anyOf"][0]["$ref"].endswith("/CreativeLatestTaskSummaryResponse")
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["input_items"]["type"] == "array"
    assert "full-carrier compatibility readback" in schemas["CreativeWorkbenchItemResponse"]["properties"]["input_items"]["description"]
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["input_orchestration"]["$ref"].endswith("/CreativeInputOrchestrationResponse")
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["pool_state"]["$ref"].endswith("/CreativeWorkbenchPoolState")
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["active_pool_item_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["active_pool_version_id"]["anyOf"][0]["type"] == "integer"
    assert schemas["CreativeWorkbenchItemResponse"]["properties"]["active_pool_aligned"]["type"] == "boolean"
    assert "input_snapshot" not in schemas["CreativeWorkbenchItemResponse"]["properties"]
    assert schemas["CreativeWorkbenchListResponse"]["properties"]["summary"]["$ref"].endswith("/CreativeWorkbenchSummaryResponse")
    assert schemas["CreativeWorkbenchSummaryResponse"]["properties"]["all_count"]["type"] == "integer"
    assert schemas["CreativeWorkbenchSummaryResponse"]["properties"]["active_pool_count"]["type"] == "integer"
    assert schemas["CreativeVersionSummaryResponse"]["properties"]["package_record"]["anyOf"][0]["$ref"].endswith("/PackageRecordResponse")
    assert schemas["CreativeVersionSummaryResponse"]["properties"]["final_product_name"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeVersionSummaryResponse"]["properties"]["final_copywriting_text"]["anyOf"][0]["type"] == "string"
    assert schemas["CreativeVersionSummaryResponse"]["properties"]["actual_duration_seconds"]["anyOf"][0]["type"] == "integer"
    assert schemas["PackageRecordResponse"]["properties"]["frozen_product_name"]["anyOf"][0]["type"] == "string"
    assert schemas["PackageRecordResponse"]["properties"]["frozen_copywriting_text"]["anyOf"][0]["type"] == "string"
    assert schemas["PackageRecordResponse"]["properties"]["frozen_duration_seconds"]["anyOf"][0]["type"] == "integer"
    assert schemas["PackageRecordResponse"]["properties"]["publish_profile_id"]["anyOf"][0]["type"] == "integer"


@pytest.mark.asyncio
async def test_frontend_exported_openapi_keeps_phase4_creative_contract_in_sync(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    live_spec = response.json()
    exported_spec = _load_exported_openapi()
    live_schemas = live_spec["components"]["schemas"]
    exported_schemas = exported_spec["components"]["schemas"]

    for schema_name in PHASE1_CREATIVE_SCHEMA_NAMES:
        assert schema_name in exported_schemas
        assert _schema_property_names(exported_spec, schema_name) == _schema_property_names(live_spec, schema_name)

    for schema_name in PHASE1_CREATIVE_ENUM_SCHEMA_NAMES:
        assert exported_schemas[schema_name] == live_schemas[schema_name]

    assert "CreativeInputSnapshotResponse" not in exported_schemas
    assert "CreativeInputSnapshotResponse" not in live_schemas

    assert _schema_refs(
        exported_spec,
        "CreativeDetailResponse",
        PHASE1_CREATIVE_DETAIL_REF_FIELDS,
    ) == _schema_refs(
        live_spec,
        "CreativeDetailResponse",
        PHASE1_CREATIVE_DETAIL_REF_FIELDS,
    )
    assert _schema_refs(
        exported_spec,
        "CreativeWorkbenchItemResponse",
        PHASE1_CREATIVE_DETAIL_REF_FIELDS,
    ) == _schema_refs(
        live_spec,
        "CreativeWorkbenchItemResponse",
        PHASE1_CREATIVE_DETAIL_REF_FIELDS,
    )

    for schema_name in ("CreativeCreateRequest", "CreativeUpdateRequest"):
        for field_name in PHASE2_LEGACY_CREATIVE_WRITE_FIELDS:
            exported_property = _schema_property(exported_spec, schema_name, field_name)
            live_property = _schema_property(live_spec, schema_name, field_name)
            assert exported_property.get("description") == live_property.get("description")
            assert exported_property.get("deprecated") == live_property.get("deprecated")

        exported_input_items = _schema_property(exported_spec, schema_name, "input_items")
        live_input_items = _schema_property(live_spec, schema_name, "input_items")
        assert exported_input_items.get("type", exported_input_items.get("anyOf")) == live_input_items.get(
            "type", live_input_items.get("anyOf")
        )


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
    assert "READY_TO_COMPOSE" in schemas["CreativeStatus"]["enum"]
    assert "FAILED" in schemas["CreativeStatus"]["enum"]
    assert "REWORK_REQUIRED" in schemas["CreativeReviewConclusion"]["enum"]


@pytest.mark.asyncio
async def test_creative_workflow_openapi_exposes_phase_d_submit_contract(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    paths = spec["paths"]
    schemas = spec["components"]["schemas"]

    submit_path = paths["/api/creative-workflows/{creative_id}/ai-clip/submit"]["post"]
    request_schema = submit_path["requestBody"]["content"]["application/json"]["schema"]
    response_schema = submit_path["responses"]["200"]["content"]["application/json"]["schema"]

    assert request_schema["$ref"].endswith("/CreativeAIClipWorkflowSubmitRequest")
    assert response_schema["$ref"].endswith("/CreativeAIClipWorkflowResponse")
    assert schemas["CreativeAIClipWorkflowSubmitRequest"]["properties"]["output_path"]["type"] == "string"
    assert schemas["CreativeAIClipWorkflowSubmitRequest"]["properties"]["source_version_id"]["type"] == "integer"
    assert schemas["CreativeAIClipWorkflowResponse"]["properties"]["workflow_type"]["type"] == "string"
    assert schemas["CreativeAIClipWorkflowResponse"]["properties"]["version"]["$ref"].endswith("/CreativeVersionSummaryResponse")
    assert schemas["CreativeAIClipWorkflowResponse"]["properties"]["package_record"]["$ref"].endswith("/PackageRecordResponse")


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
