import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from utils.time import utc_now_naive
from datetime import timedelta

from models import Account, Audio, Copywriting, Cover, CreativeItem, CreativeVersion, Product, PublishPoolItem, PublishProfile, Task, Topic, Video
from services.creative_version_service import CreativeVersionService
from services.creative_service import CreativeService


async def _seed_creative_sample(
    db_session: AsyncSession,
    *,
    creative_no: str = "CR-API-0001",
    title: str = "Creative API Sample",
) -> tuple[int, int]:
    account = Account(
        account_id=f"creative-api-account-{creative_no.lower()}",
        account_name=f"Creative API Account {creative_no}",
    )
    db_session.add(account)
    await db_session.flush()

    task = Task(account_id=account.id, status="draft", name="Creative API sample task")
    db_session.add(task)
    await db_session.commit()

    service = CreativeService(db_session)
    mapped_task = await service.attach_task_to_creative_sample(
        task.id,
        creative_no=creative_no,
        title=title,
    )
    creative = await db_session.get(CreativeItem, mapped_task.creative_item_id)
    assert creative is not None
    creative.subject_product_name_snapshot = "Creative API Product"
    creative.main_copywriting_text = "Creative API Copy"
    version = await db_session.get(CreativeVersion, creative.current_version_id)
    assert version is not None
    version_service = CreativeVersionService(db_session)
    await version_service.sync_version_result(
        version,
        final_product_name="Creative API Product",
        final_copywriting_text="Creative API Copy",
    )
    await version_service.sync_publish_package(
        version,
        frozen_product_name="Creative API Product",
        frozen_copywriting_text="Creative API Copy",
    )
    await db_session.commit()
    await db_session.refresh(mapped_task)
    return mapped_task.creative_item_id, mapped_task.id


async def _seed_profile_and_materials(
    db_session: AsyncSession,
    *,
    composition_mode: str = "none",
) -> tuple[PublishProfile, Video, Audio, Topic]:
    profile = PublishProfile(
        name=f"creative-profile-{composition_mode}",
        composition_mode=composition_mode,
        composition_params="{}",
    )
    video = Video(name="creative-video", file_path="data/videos/creative-video.mp4")
    audio = Audio(name="creative-audio", file_path="data/audios/creative-audio.mp3")
    topic = Topic(name=f"creative-topic-{composition_mode}")
    db_session.add_all([profile, video, audio, topic])
    await db_session.commit()
    await db_session.refresh(profile)
    await db_session.refresh(video)
    await db_session.refresh(audio)
    await db_session.refresh(topic)
    return profile, video, audio, topic


async def _seed_domain_inputs(
    db_session: AsyncSession,
    *,
    composition_mode: str = "none",
) -> tuple[PublishProfile, Product, Video, Copywriting, Cover, Audio, Topic]:
    profile = PublishProfile(
        name=f"creative-phase1-profile-{composition_mode}",
        composition_mode=composition_mode,
        composition_params="{}",
    )
    product = Product(name=f"creative-phase1-product-{composition_mode}")
    video = Video(name=f"creative-phase1-video-{composition_mode}", file_path=f"data/videos/{composition_mode}.mp4")
    copywriting = Copywriting(name=f"creative-phase1-copy-{composition_mode}", content="phase1 copy", source_type="manual")
    cover = Cover(name=f"creative-phase1-cover-{composition_mode}", file_path=f"data/covers/{composition_mode}.png")
    audio = Audio(name=f"creative-phase1-audio-{composition_mode}", file_path=f"data/audios/{composition_mode}.mp3")
    topic = Topic(name=f"creative-phase1-topic-{composition_mode}")
    db_session.add_all([profile, product, video, copywriting, cover, audio, topic])
    await db_session.commit()
    for item in (profile, product, video, copywriting, cover, audio, topic):
        await db_session.refresh(item)
    return profile, product, video, copywriting, cover, audio, topic


@pytest.mark.asyncio
async def test_list_creatives_returns_empty_state(client: AsyncClient) -> None:
    response = await client.get("/api/creatives")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "items": [],
        "summary": {
            "all_count": 0,
            "waiting_review_count": 0,
            "pending_input_count": 0,
            "needs_rework_count": 0,
            "recent_failures_count": 0,
            "active_pool_count": 0,
            "aligned_pool_count": 0,
            "version_mismatch_count": 0,
        },
    }


@pytest.mark.asyncio
async def test_get_creative_returns_404_for_missing_record(client: AsyncClient) -> None:
    response = await client.get("/api/creatives/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_creative_allows_work_item_without_current_version(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/creatives",
        json={"title": "作品驱动样例"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "作品驱动样例"
    assert payload["current_version_id"] is None
    assert payload["current_version"] is None
    assert payload["versions"] == []
    assert payload["status"] == "PENDING_INPUT"
    assert payload["eligibility_status"] == "PENDING_INPUT"
    assert payload["input_orchestration"]["profile_id"] is None
    assert payload["input_orchestration"]["item_count"] == 0
    assert payload["input_orchestration"]["enabled_item_count"] == 0
    assert len(payload["input_orchestration"]["orchestration_hash"]) == 64
    assert "input_snapshot" not in payload
    assert "请选择合成配置" in payload["eligibility_reasons"]
    assert "至少选择 1 个视频" in payload["eligibility_reasons"]


@pytest.mark.asyncio
async def test_create_creative_can_project_ready_to_compose_from_input_items(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, _, topic = await _seed_profile_and_materials(db_session, composition_mode="none")

    response = await client.post(
        "/api/creatives",
        json={
            "title": "Ready Creative",
            "profile_id": profile.id,
            "input_items": [
                {"material_type": "video", "material_id": video.id},
                {"material_type": "topic", "material_id": topic.id},
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "READY_TO_COMPOSE"
    assert payload["eligibility_status"] == "READY_TO_COMPOSE"
    assert payload["eligibility_reasons"] == []
    assert payload["input_orchestration"]["profile_id"] == profile.id
    assert payload["input_orchestration"]["item_count"] == 2
    assert payload["input_orchestration"]["enabled_item_count"] == 2
    assert payload["input_orchestration"]["material_counts"]["video"] == 1
    assert payload["input_orchestration"]["material_counts"]["topic"] == 1
    assert "input_snapshot" not in payload


@pytest.mark.asyncio
async def test_create_creative_dual_writes_authoritative_input_items_and_legacy_snapshot_carriers(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, product, video, copywriting, cover, audio, topic = await _seed_domain_inputs(
        db_session,
        composition_mode="coze",
    )

    response = await client.post(
        "/api/creatives",
        json={
            "title": "Creative Phase1 PR2",
            "subject_product_id": product.id,
            "main_copywriting_text": "authoritative copy brief",
            "target_duration_seconds": 45,
            "profile_id": profile.id,
            "input_items": [
                {"material_type": "video", "material_id": video.id, "role": "opening", "trim_in": 0, "trim_out": 8},
                {"material_type": "video", "material_id": video.id, "role": "ending", "trim_in": 9, "trim_out": 16},
                {"material_type": "copywriting", "material_id": copywriting.id},
                {"material_type": "cover", "material_id": cover.id},
                {"material_type": "audio", "material_id": audio.id},
                {"material_type": "topic", "material_id": topic.id},
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["subject_product_id"] == product.id
    assert payload["subject_product_name_snapshot"] == product.name
    assert payload["main_copywriting_text"] == "authoritative copy brief"
    assert payload["target_duration_seconds"] == 45
    assert [item["material_type"] for item in payload["input_items"]] == [
        "video",
        "video",
        "copywriting",
        "cover",
        "audio",
        "topic",
    ]
    assert [item["material_id"] for item in payload["input_items"][:2]] == [video.id, video.id]
    assert [item["instance_no"] for item in payload["input_items"][:2]] == [1, 2]
    assert [item["role"] for item in payload["input_items"][:2]] == ["opening", "ending"]
    assert payload["input_orchestration"]["profile_id"] == profile.id
    assert payload["input_orchestration"]["item_count"] == 6
    assert payload["input_orchestration"]["enabled_item_count"] == 6
    assert payload["input_orchestration"]["material_counts"]["video"] == 2
    assert payload["input_orchestration"]["enabled_material_counts"]["audio"] == 1
    assert "input_snapshot" not in payload


@pytest.mark.asyncio
async def test_creative_patch_does_not_silently_deduplicate_repeated_input_items(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, _, video, _, _, _, _ = await _seed_domain_inputs(
        db_session,
        composition_mode="coze",
    )
    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Creative Patch",
            "profile_id": profile.id,
            "input_items": [{"material_type": "video", "material_id": video.id}],
        },
    )
    assert create_response.status_code == 201
    creative = create_response.json()

    patch_response = await client.patch(
        f"/api/creatives/{creative['id']}",
        json={
            "input_items": [
                {"material_type": "video", "material_id": video.id, "role": "opening"},
                {"material_type": "video", "material_id": video.id, "role": "ending"},
            ]
        },
    )

    assert patch_response.status_code == 200
    payload = patch_response.json()
    assert [item["material_id"] for item in payload["input_items"]] == [video.id, video.id]
    assert [item["instance_no"] for item in payload["input_items"]] == [1, 2]
    assert [item["role"] for item in payload["input_items"]] == ["opening", "ending"]
    assert payload["input_orchestration"]["material_counts"]["video"] == 2


@pytest.mark.asyncio
async def test_submit_composition_reports_execution_layer_limitation_for_duplicate_instances(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, _, video, _, _, _, _ = await _seed_domain_inputs(
        db_session,
        composition_mode="coze",
    )
    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Creative Submit Limitation",
            "profile_id": profile.id,
            "input_items": [
                {"material_type": "video", "material_id": video.id, "role": "opening"},
                {"material_type": "video", "material_id": video.id, "role": "ending"},
            ],
        },
    )
    assert create_response.status_code == 201
    creative = create_response.json()
    assert creative["eligibility_status"] == "INVALID"
    assert any("执行路径暂不支持" in reason for reason in creative["eligibility_reasons"])

    submit_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")

    assert submit_response.status_code == 400
    assert "执行路径暂不支持" in submit_response.json()["detail"]


@pytest.mark.asyncio
async def test_create_creative_rejects_legacy_list_write_fields_in_phase2(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, _, video, _, _, _, topic = await _seed_domain_inputs(
        db_session,
        composition_mode="coze",
    )
    response = await client.post(
        "/api/creatives",
        json={
            "title": "Legacy Carrier Reject",
            "profile_id": profile.id,
            "video_ids": [video.id],
            "topic_ids": [topic.id],
        },
    )

    assert response.status_code == 422
    assert "Phase 2 creative write requests must use input_items" in response.text


@pytest.mark.asyncio
async def test_creative_patch_rejects_legacy_list_write_fields_in_phase2(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, _, video, _, _, _, topic = await _seed_domain_inputs(
        db_session,
        composition_mode="coze",
    )
    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Legacy Patch Reject",
            "profile_id": profile.id,
            "input_items": [
                {"material_type": "video", "material_id": video.id},
                {"material_type": "topic", "material_id": topic.id},
            ],
        },
    )
    assert create_response.status_code == 201
    creative = create_response.json()

    patch_response = await client.patch(
        f"/api/creatives/{creative['id']}",
        json={"video_ids": [video.id]},
    )

    assert patch_response.status_code == 422
    assert "Phase 2 creative write requests must use input_items" in patch_response.text


@pytest.mark.asyncio
async def test_creative_update_can_change_orchestration_hash_and_mark_invalid_combo(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, audio, _ = await _seed_profile_and_materials(db_session, composition_mode="none")

    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Patch Creative",
            "profile_id": profile.id,
            "input_items": [{"material_type": "video", "material_id": video.id}],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    patch_response = await client.patch(
        f"/api/creatives/{created['id']}",
        json={
            "input_items": [
                {"material_type": "video", "material_id": video.id},
                {"material_type": "audio", "material_id": audio.id},
            ]
        },
    )

    assert patch_response.status_code == 200
    payload = patch_response.json()
    assert payload["eligibility_status"] == "INVALID"
    assert payload["status"] == "PENDING_INPUT"
    assert payload["input_orchestration"]["material_counts"]["audio"] == 1
    assert payload["input_orchestration"]["orchestration_hash"] != created["input_orchestration"]["orchestration_hash"]
    assert "input_snapshot" not in payload
    assert any("独立音频输入" in reason for reason in payload["eligibility_reasons"])


@pytest.mark.asyncio
async def test_creative_detail_projects_composing_from_task_execution_state(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, _, _ = await _seed_profile_and_materials(db_session, composition_mode="none")
    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Composing Creative",
            "profile_id": profile.id,
            "input_items": [{"material_type": "video", "material_id": video.id}],
        },
    )
    assert create_response.status_code == 201
    creative = create_response.json()

    task = Task(
        status="composing",
        name="Work-driven compose",
        creative_item_id=creative["id"],
        task_kind="composition",
    )
    db_session.add(task)
    await db_session.commit()

    detail_response = await client.get(f"/api/creatives/{creative['id']}")

    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["status"] == "COMPOSING"
    assert payload["eligibility_status"] == "READY_TO_COMPOSE"
    assert payload["latest_task_summary"]["task_id"] == task.id
    assert payload["latest_task_summary"]["task_kind"] == "composition"
    assert payload["latest_task_summary"]["task_status"] == "composing"


@pytest.mark.asyncio
async def test_creative_list_and_detail_return_phase_a_projection(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, task_id = await _seed_creative_sample(db_session)

    list_response = await client.get("/api/creatives")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["summary"]["all_count"] == 1
    assert list_payload["summary"]["active_pool_count"] == 0
    assert list_payload["items"][0]["id"] == creative_id
    assert list_payload["items"][0]["creative_no"] == "CR-API-0001"
    assert list_payload["items"][0]["title"] == "Creative API Sample"
    assert list_payload["items"][0]["status"] == "PENDING_INPUT"
    assert list_payload["items"][0]["current_version_id"] is not None
    assert list_payload["items"][0]["pool_state"] == "out_pool"
    assert list_payload["items"][0]["active_pool_item_id"] is None
    assert list_payload["items"][0]["active_pool_version_id"] is None
    assert list_payload["items"][0]["active_pool_aligned"] is False

    detail_response = await client.get(f"/api/creatives/{creative_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == creative_id
    assert detail_payload["creative_no"] == "CR-API-0001"
    assert detail_payload["current_version"]["version_no"] == 1
    assert detail_payload["current_version"]["title"] == "Creative API Sample"
    assert detail_payload["current_version"]["final_product_name"] == "Creative API Product"
    assert detail_payload["current_version"]["final_copywriting_text"] == "Creative API Copy"
    assert detail_payload["current_version"]["package_record_id"] is not None
    assert detail_payload["current_version"]["package_record"]["frozen_product_name"] == "Creative API Product"
    assert detail_payload["current_version"]["package_record"]["frozen_copywriting_text"] == "Creative API Copy"
    assert detail_payload["linked_task_ids"] == [task_id]


@pytest.mark.asyncio
async def test_task_detail_remains_compatible_after_creative_attach_helper(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    creative_id, task_id = await _seed_creative_sample(db_session)

    response = await client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_item_id"] == creative_id
    assert payload["creative_version_id"] is not None
    assert payload["task_kind"] == "composition"


@pytest.mark.asyncio
async def test_list_creatives_supports_service_side_filters_and_summary(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    alpha_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0101",
        title="Alpha Review",
    )
    beta_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0102",
        title="Beta Failure",
    )
    gamma_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0103",
        title="Gamma Draft",
    )
    delta_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0104",
        title="Delta Pool",
    )

    alpha = await db_session.get(CreativeItem, alpha_id)
    beta = await db_session.get(CreativeItem, beta_id)
    gamma = await db_session.get(CreativeItem, gamma_id)
    delta = await db_session.get(CreativeItem, delta_id)
    assert alpha is not None
    assert beta is not None
    assert gamma is not None
    assert delta is not None

    now = utc_now_naive()

    alpha.status = "WAITING_REVIEW"
    alpha.updated_at = now - timedelta(hours=2)
    beta.status = "REWORK_REQUIRED"
    beta.generation_error_msg = "boom"
    beta.generation_failed_at = now - timedelta(minutes=5)
    beta.updated_at = now - timedelta(minutes=10)
    gamma.status = "PENDING_INPUT"
    gamma.current_version_id = None
    gamma.updated_at = now - timedelta(hours=1)
    delta.status = "APPROVED"
    delta.updated_at = now - timedelta(minutes=30)

    db_session.add_all([
        PublishPoolItem(
            creative_item_id=beta.id,
            creative_version_id=beta.current_version_id,
            status="active",
        ),
        PublishPoolItem(
            creative_item_id=delta.id,
            creative_version_id=delta.current_version_id,
            status="active",
        ),
    ])
    beta.current_version_id = None
    await db_session.commit()

    response = await client.get(
        "/api/creatives",
        params={
            "keyword": "beta",
            "status": "REWORK_REQUIRED",
            "pool_state": "version_mismatch",
            "recent_failures_only": "true",
            "sort": "failed_desc",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["id"] for item in payload["items"]] == [beta_id]
    assert payload["items"][0]["pool_state"] == "version_mismatch"
    assert payload["items"][0]["active_pool_item_id"] is not None
    assert payload["items"][0]["active_pool_aligned"] is False
    assert payload["summary"] == {
        "all_count": 4,
        "waiting_review_count": 1,
        "pending_input_count": 1,
        "needs_rework_count": 1,
        "recent_failures_count": 1,
        "active_pool_count": 2,
        "aligned_pool_count": 1,
        "version_mismatch_count": 1,
    }


@pytest.mark.asyncio
async def test_list_creatives_supports_service_side_sort_and_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    alpha_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0201",
        title="Alpha Review",
    )
    beta_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0202",
        title="Beta Failure",
    )
    gamma_id, _ = await _seed_creative_sample(
        db_session,
        creative_no="CR-API-0203",
        title="Gamma Draft",
    )

    alpha = await db_session.get(CreativeItem, alpha_id)
    beta = await db_session.get(CreativeItem, beta_id)
    gamma = await db_session.get(CreativeItem, gamma_id)
    assert alpha is not None
    assert beta is not None
    assert gamma is not None

    now = utc_now_naive()
    alpha.status = "WAITING_REVIEW"
    alpha.updated_at = now - timedelta(hours=2)
    beta.status = "REWORK_REQUIRED"
    beta.generation_error_msg = "boom"
    beta.generation_failed_at = now - timedelta(minutes=5)
    beta.updated_at = now - timedelta(minutes=10)
    gamma.status = "PENDING_INPUT"
    gamma.updated_at = now - timedelta(hours=1)

    db_session.add_all([
        PublishPoolItem(
            creative_item_id=beta.id,
            creative_version_id=beta.current_version_id,
            status="active",
        ),
    ])
    beta.current_version_id = None
    await db_session.commit()

    attention_response = await client.get("/api/creatives", params={"sort": "attention_desc"})
    assert attention_response.status_code == 200
    assert [item["id"] for item in attention_response.json()["items"]] == [beta_id, alpha_id, gamma_id]

    page_response = await client.get("/api/creatives", params={"sort": "updated_desc", "skip": 1, "limit": 1})
    assert page_response.status_code == 200
    assert page_response.json()["total"] == 3
    assert len(page_response.json()["items"]) == 1
    assert page_response.json()["items"][0]["id"] == gamma_id
