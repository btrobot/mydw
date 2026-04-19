"""
Phase 6 / PR2: legacy runtime dependency fence tests.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Account,
    Audio,
    Copywriting,
    PublishProfile,
    Task,
    TaskAudio,
    TaskCopywriting,
    TaskVideo,
    Video,
)
from services.composition_service import CompositionService
from services.task_compat_service import (
    count_tasks_referencing_copywriting,
    count_tasks_referencing_video,
    resolve_primary_task_audio,
    resolve_primary_task_video,
)


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"legacy_fence_{suffix}",
        account_name=f"Legacy Fence {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_video(db: AsyncSession, suffix: str) -> Video:
    video = Video(name=f"video_{suffix}.mp4", file_path=f"videos/video_{suffix}.mp4")
    db.add(video)
    await db.flush()
    return video


async def _create_copywriting(db: AsyncSession, suffix: str) -> Copywriting:
    copywriting = Copywriting(name=f"cw_{suffix}", content=f"文案 {suffix}")
    db.add(copywriting)
    await db.flush()
    return copywriting


async def _create_audio(db: AsyncSession, suffix: str) -> Audio:
    audio = Audio(name=f"audio_{suffix}.mp3", file_path=f"audios/audio_{suffix}.mp3")
    db.add(audio)
    await db.flush()
    return audio


async def _create_profile(db: AsyncSession, suffix: str) -> PublishProfile:
    profile = PublishProfile(
        name=f"profile_{suffix}",
        composition_mode="coze",
        coze_workflow_id=f"wf_{suffix}",
    )
    db.add(profile)
    await db.flush()
    return profile


@pytest.mark.asyncio
async def test_task_reference_counters_cover_relation_tables_and_legacy_columns(
    db_session: AsyncSession,
) -> None:
    account = await _create_account(db_session, "counter")
    legacy_video = await _create_video(db_session, "legacy_video")
    relation_video = await _create_video(db_session, "relation_video")
    relation_copywriting = await _create_copywriting(db_session, "relation_cw")
    legacy_copywriting = await _create_copywriting(db_session, "legacy_cw")

    legacy_task = Task(
        account_id=account.id,
        status="draft",
        video_id=legacy_video.id,
        copywriting_id=legacy_copywriting.id,
    )
    relation_task = Task(account_id=account.id, status="draft")
    mixed_task = Task(account_id=account.id, status="draft", video_id=relation_video.id)
    db_session.add_all([legacy_task, relation_task, mixed_task])
    await db_session.flush()

    db_session.add(TaskVideo(task_id=relation_task.id, video_id=relation_video.id, sort_order=0))
    db_session.add(TaskVideo(task_id=mixed_task.id, video_id=relation_video.id, sort_order=0))
    db_session.add(TaskCopywriting(task_id=relation_task.id, copywriting_id=relation_copywriting.id, sort_order=0))
    await db_session.commit()

    assert await count_tasks_referencing_video(db_session, legacy_video.id) == 1
    assert await count_tasks_referencing_video(db_session, relation_video.id) == 2
    assert await count_tasks_referencing_copywriting(db_session, legacy_copywriting.id) == 1
    assert await count_tasks_referencing_copywriting(db_session, relation_copywriting.id) == 1


@pytest.mark.asyncio
async def test_resolve_primary_task_video_prefers_relation_table_but_falls_back_to_legacy(
    db_session: AsyncSession,
) -> None:
    account = await _create_account(db_session, "resolve_video")
    legacy_video = await _create_video(db_session, "legacy_only")
    relation_video = await _create_video(db_session, "relation_first")

    relation_task = Task(account_id=account.id, status="draft", video_id=legacy_video.id)
    legacy_only_task = Task(account_id=account.id, status="draft", video_id=legacy_video.id)
    db_session.add_all([relation_task, legacy_only_task])
    await db_session.flush()
    db_session.add(TaskVideo(task_id=relation_task.id, video_id=relation_video.id, sort_order=0))
    await db_session.commit()

    preferred = await resolve_primary_task_video(db_session, relation_task)
    fallback = await resolve_primary_task_video(db_session, legacy_only_task)

    assert preferred is not None
    assert preferred.id == relation_video.id
    assert fallback is not None
    assert fallback.id == legacy_video.id


@pytest.mark.asyncio
async def test_resolve_primary_task_audio_prefers_relation_table_but_falls_back_to_legacy(
    db_session: AsyncSession,
) -> None:
    account = await _create_account(db_session, "resolve_audio")
    legacy_audio = await _create_audio(db_session, "legacy_only")
    relation_audio = await _create_audio(db_session, "relation_first")

    relation_task = Task(account_id=account.id, status="draft", audio_id=legacy_audio.id)
    legacy_only_task = Task(account_id=account.id, status="draft", audio_id=legacy_audio.id)
    db_session.add_all([relation_task, legacy_only_task])
    await db_session.flush()
    db_session.add(TaskAudio(task_id=relation_task.id, audio_id=relation_audio.id, sort_order=0))
    await db_session.commit()

    preferred = await resolve_primary_task_audio(db_session, relation_task)
    fallback = await resolve_primary_task_audio(db_session, legacy_only_task)

    assert preferred is not None
    assert preferred.id == relation_audio.id
    assert fallback is not None
    assert fallback.id == legacy_audio.id


@pytest.mark.asyncio
async def test_delete_guards_block_relation_table_references(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    account = await _create_account(db_session, "delete_guard")
    video = await _create_video(db_session, "guard_video")
    copywriting = await _create_copywriting(db_session, "guard_cw")
    task = Task(account_id=account.id, status="draft")
    db_session.add(task)
    await db_session.flush()
    db_session.add(TaskVideo(task_id=task.id, video_id=video.id, sort_order=0))
    db_session.add(TaskCopywriting(task_id=task.id, copywriting_id=copywriting.id, sort_order=0))
    await db_session.commit()

    video_resp = await client.delete(f"/api/videos/{video.id}")
    copywriting_resp = await client.delete(f"/api/copywritings/{copywriting.id}")

    assert video_resp.status_code == 409
    assert "任务引用" in video_resp.json()["detail"]
    assert copywriting_resp.status_code == 409
    assert "任务引用" in copywriting_resp.json()["detail"]


@pytest.mark.asyncio
async def test_submit_composition_uses_relation_video_without_legacy_video_id(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = await _create_account(db_session, "composition")
    relation_video = await _create_video(db_session, "composition_source")
    profile = await _create_profile(db_session, "composition")

    task = Task(account_id=account.id, status="draft", profile_id=profile.id)
    db_session.add(task)
    await db_session.flush()
    db_session.add(TaskVideo(task_id=task.id, video_id=relation_video.id, sort_order=0))
    await db_session.commit()

    coze_client = MagicMock()
    coze_client.upload_file = AsyncMock(return_value="file_123")
    coze_client.submit_composition = AsyncMock(return_value="job_456")
    monkeypatch.setattr("services.composition_service.CozeClient", lambda: coze_client)

    service = CompositionService(db_session)
    job = await service.submit_composition(task.id)

    assert job.external_job_id == "job_456"
    coze_client.upload_file.assert_awaited_once_with(relation_video.file_path)
    coze_client.submit_composition.assert_awaited_once()
