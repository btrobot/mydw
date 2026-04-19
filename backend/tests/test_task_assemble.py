"""
Phase 2 / PR1: 任务语义基线测试

验证当前 authoritative contract：
- 任务响应以 collection-based `*_ids` 字段为主
- `/api/tasks/assemble` 是兼容入口，但仍遵守资源集合模型
- `/api/tasks/` 的 public create contract 已切到 `TaskCreateRequest`
- legacy 单资源 FK 请求不再视为主 contract
- Phase 6 / PR1 追加冻结当前 topic semantics：
  - TaskAssembler 自动合并 profile-level default topics
  - `/api/topics/global` 仍是 legacy singleton topic surface，不会自动注入 task assembly
"""
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, Video, Copywriting, Product, Audio, Cover, Topic, PublishProfile, TaskVideo


# ============ 辅助函数 ============

async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"acct_{suffix}",
        account_name=f"Account {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_video(
    db: AsyncSession,
    suffix: str,
    product_id: int | None = None,
) -> Video:
    video = Video(
        name=f"video_{suffix}.mp4",
        file_path=f"videos/video_{suffix}.mp4",
        product_id=product_id,
    )
    db.add(video)
    await db.flush()
    return video


async def _create_product(db: AsyncSession, name: str) -> Product:
    product = Product(name=name)
    db.add(product)
    await db.flush()
    return product


async def _create_copywriting(
    db: AsyncSession,
    content: str,
    product_id: int | None = None,
) -> Copywriting:
    cw = Copywriting(name=content[:20], content=content, product_id=product_id)
    db.add(cw)
    await db.flush()
    return cw


async def _create_cover(db: AsyncSession, suffix: str) -> Cover:
    cover = Cover(name=f"cover_{suffix}", file_path=f"covers/cover_{suffix}.jpg")
    db.add(cover)
    await db.flush()
    return cover


async def _create_audio(db: AsyncSession, suffix: str) -> Audio:
    audio = Audio(name=f"audio_{suffix}", file_path=f"audios/audio_{suffix}.mp3")
    db.add(audio)
    await db.flush()
    return audio


async def _create_topic(db: AsyncSession, suffix: str) -> Topic:
    topic = Topic(name=f"topic_{suffix}")
    db.add(topic)
    await db.flush()
    return topic


async def _create_profile(
    db: AsyncSession,
    name: str,
    composition_mode: str,
    *,
    global_topic_ids: list[int] | None = None,
) -> PublishProfile:
    profile = PublishProfile(
        name=name,
        composition_mode=composition_mode,
        is_default=False,
        global_topic_ids=json.dumps(global_topic_ids or []),
    )
    db.add(profile)
    await db.flush()
    return profile


async def _get_all_tasks(client: AsyncClient) -> list[dict]:
    """GET /api/tasks/ 使用 selectinload，不触发 BUG-001。"""
    resp = await client.get("/api/tasks/")
    assert resp.status_code == 200
    return resp.json()["items"]


# ============ 测试用例 ============

@pytest.mark.asyncio
async def test_assemble_tasks(client: AsyncClient, db_session: AsyncSession) -> None:
    """valid direct publish：1 Video + 2 Account → 生成 2 个 ready task。"""
    acct1 = await _create_account(db_session, "a1")
    acct2 = await _create_account(db_session, "a2")
    vid1 = await _create_video(db_session, "v1")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid1.id],
            "account_ids": [acct1.id, acct2.id],
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 2
    for task in tasks:
        assert task["account_id"] in {acct1.id, acct2.id}
        assert task["video_ids"] == [vid1.id]
        assert task["copywriting_ids"] == []
        assert task["cover_ids"] == []
        assert task["audio_ids"] == []
        assert task["topic_ids"] == []
        assert task["status"] == "ready"


@pytest.mark.asyncio
async def test_assemble_ignores_legacy_strategy_and_keeps_collection_semantics(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """legacy strategy 字段不会绕过 direct publish 语义校验。"""
    acct1 = await _create_account(db_session, "rr_a1")
    acct2 = await _create_account(db_session, "rr_a2")
    vid1 = await _create_video(db_session, "rr_v1")
    vid2 = await _create_video(db_session, "rr_v2")
    vid3 = await _create_video(db_session, "rr_v3")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid1.id, vid2.id, vid3.id],
            "account_ids": [acct1.id, acct2.id],
            "strategy": "round_robin",
        },
    )
    assert resp.status_code == 400
    assert "仅支持 1 个最终视频" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_tasks_returns_collection_ids_for_all_selected_resources(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """`POST /api/tasks/` 以 TaskCreateRequest 为 authoritative create contract。"""
    product = await _create_product(db_session, "prod_collection_test")
    acct = await _create_account(db_session, "collection_a1")
    vid = await _create_video(db_session, "collection_v1", product_id=product.id)
    cw = await _create_copywriting(db_session, "测试文案内容", product_id=product.id)
    cover = await _create_cover(db_session, "collection_c1")
    topic = await _create_topic(db_session, "collection_t1")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid.id],
            "copywriting_ids": [cw.id],
            "cover_ids": [cover.id],
            "audio_ids": [],
            "topic_ids": [topic.id],
            "account_ids": [acct.id],
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["video_ids"] == [vid.id]
    assert tasks[0]["copywriting_ids"] == [cw.id]
    assert tasks[0]["cover_ids"] == [cover.id]
    assert tasks[0]["audio_ids"] == []
    assert tasks[0]["topic_ids"] == [topic.id]
    assert tasks[0]["status"] == "ready"


@pytest.mark.asyncio
async def test_create_tasks_allows_missing_account_and_keeps_task_unassigned(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = await _create_video(db_session, "collection_no_account_v1")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid.id],
            "copywriting_ids": [],
            "cover_ids": [],
            "audio_ids": [],
            "topic_ids": [],
            "account_ids": [],
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["account_id"] is None
    assert tasks[0]["video_ids"] == [vid.id]
    assert tasks[0]["status"] == "ready"


@pytest.mark.asyncio
async def test_create_tasks_with_composition_profile_start_in_draft(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """composition profile 存在时，任务状态按 profile 语义进入 draft。"""
    acct = await _create_account(db_session, "profile_a1")
    vid1 = await _create_video(db_session, "profile_v1")
    vid2 = await _create_video(db_session, "profile_v2")
    profile = await _create_profile(db_session, "coze-profile", "coze")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid1.id, vid2.id],
            "account_ids": [acct.id],
            "profile_id": profile.id,
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["video_ids"] == [vid1.id, vid2.id]
    assert tasks[0]["status"] == "draft"


@pytest.mark.asyncio
async def test_create_tasks_with_local_ffmpeg_profile_accepts_v1_input_and_starts_in_draft(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    acct = await _create_account(db_session, "profile_ffmpeg_a1")
    vid = await _create_video(db_session, "profile_ffmpeg_v1")
    audio = await _create_audio(db_session, "profile_ffmpeg_audio")
    profile = await _create_profile(db_session, "local-ffmpeg-profile", "local_ffmpeg")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid.id],
            "audio_ids": [audio.id],
            "copywriting_ids": [],
            "cover_ids": [],
            "topic_ids": [],
            "account_ids": [acct.id],
            "profile_id": profile.id,
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "draft"
    assert tasks[0]["video_ids"] == [vid.id]
    assert tasks[0]["audio_ids"] == [audio.id]


@pytest.mark.asyncio
async def test_create_tasks_rejects_invalid_local_ffmpeg_combo_early(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    acct = await _create_account(db_session, "invalid_ffmpeg_a1")
    vid1 = await _create_video(db_session, "invalid_ffmpeg_v1")
    vid2 = await _create_video(db_session, "invalid_ffmpeg_v2")
    profile = await _create_profile(db_session, "invalid-ffmpeg-profile", "local_ffmpeg")
    await db_session.commit()

    response = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid1.id, vid2.id],
            "audio_ids": [],
            "copywriting_ids": [],
            "cover_ids": [],
            "topic_ids": [],
            "account_ids": [acct.id],
            "profile_id": profile.id,
        },
    )
    assert response.status_code == 400
    assert "local_ffmpeg V1 仅支持 1 个视频输入" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_task_removes_task_video_relations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    acct = await _create_account(db_session, "delete_rel_a1")
    vid = await _create_video(db_session, "delete_rel_v1")
    await db_session.commit()

    create_resp = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid.id],
            "account_ids": [acct.id],
        },
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()[0]["id"]

    delete_resp = await client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 204

    relation_count = await db_session.execute(
        select(func.count(TaskVideo.id)).where(TaskVideo.task_id == task_id)
    )
    assert relation_count.scalar() == 0


@pytest.mark.asyncio
async def test_assemble_merges_profile_default_topics_but_not_legacy_singleton_topics(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    legacy_topic = await _create_topic(db_session, "legacy_singleton")
    profile_topic = await _create_topic(db_session, "profile_default")
    acct = await _create_account(db_session, "topic_semantics_a1")
    vid = await _create_video(db_session, "topic_semantics_v1")
    profile = await _create_profile(
        db_session,
        "topic-semantics-profile",
        "none",
        global_topic_ids=[profile_topic.id],
    )
    await db_session.commit()

    set_global_resp = await client.put(
        "/api/topics/global",
        json={"topic_ids": [legacy_topic.id]},
    )
    assert set_global_resp.status_code == 200

    assemble_resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid.id],
            "account_ids": [acct.id],
            "profile_id": profile.id,
        },
    )
    assert assemble_resp.status_code == 201
    task = assemble_resp.json()[0]

    assert task["topic_ids"] == [profile_topic.id]


@pytest.mark.asyncio
async def test_create_tasks_reject_direct_publish_audio_and_multiple_copywritings(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """direct publish invalid combinations should fail early at create time."""
    acct = await _create_account(db_session, "invalid_direct_a1")
    vid = await _create_video(db_session, "invalid_direct_v1")
    cw1 = await _create_copywriting(db_session, "文案一")
    cw2 = await _create_copywriting(db_session, "文案二")
    audio = await _create_audio(db_session, "invalid_direct_audio")
    await db_session.commit()

    response = await client.post(
        "/api/tasks/",
        json={
            "video_ids": [vid.id],
            "copywriting_ids": [cw1.id, cw2.id],
            "audio_ids": [audio.id],
            "cover_ids": [],
            "topic_ids": [],
            "account_ids": [acct.id],
        },
    )
    assert response.status_code == 400
    assert "仅支持 0 或 1 个文案" in response.json()["detail"]


@pytest.mark.asyncio
async def test_legacy_fk_style_create_request_is_rejected_by_public_contract(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """legacy 单资源 FK body 不再是 public create contract。"""
    acct = await _create_account(db_session, "legacy_a1")
    vid = await _create_video(db_session, "legacy_v1")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "account_id": acct.id,
            "video_id": vid.id,
        },
    )
    assert resp.status_code == 422
