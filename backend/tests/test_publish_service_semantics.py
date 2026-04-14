"""
Phase 2 / PR2: publish path semantics tests.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Account,
    Audio,
    Copywriting,
    Cover,
    PublishProfile,
    Task,
    TaskAudio,
    TaskCover,
    TaskCopywriting,
    TaskTopic,
    TaskVideo,
    Topic,
    Video,
)
from schemas.auth import LocalAuthSessionSummary
from services.publish_service import PublishService
from services.task_execution_semantics import (
    PublishabilityError,
    resolve_publish_execution_view,
)


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"publish_{suffix}",
        account_name=f"Publish {suffix}",
        status="active",
        storage_state="{}",
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
    cw = Copywriting(name=f"cw_{suffix}", content=f"文案 {suffix}")
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


async def _create_profile(db: AsyncSession, suffix: str, composition_mode: str) -> PublishProfile:
    profile = PublishProfile(name=f"profile_{suffix}", composition_mode=composition_mode)
    db.add(profile)
    await db.flush()
    return profile


async def _get_task(db: AsyncSession, task_id: int) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one()


async def _create_raw_task_with_resources(
    db: AsyncSession,
    *,
    account_id: int,
    video_ids: list[int],
    copywriting_ids: list[int] | None = None,
    cover_ids: list[int] | None = None,
    audio_ids: list[int] | None = None,
    topic_ids: list[int] | None = None,
    status: str = "ready",
    profile_id: int | None = None,
) -> Task:
    task = Task(account_id=account_id, status=status, profile_id=profile_id)
    db.add(task)
    await db.flush()

    for order, video_id in enumerate(video_ids):
        db.add(TaskVideo(task_id=task.id, video_id=video_id, sort_order=order))
    for order, copywriting_id in enumerate(copywriting_ids or []):
        db.add(TaskCopywriting(task_id=task.id, copywriting_id=copywriting_id, sort_order=order))
    for order, cover_id in enumerate(cover_ids or []):
        db.add(TaskCover(task_id=task.id, cover_id=cover_id, sort_order=order))
    for order, audio_id in enumerate(audio_ids or []):
        db.add(TaskAudio(task_id=task.id, audio_id=audio_id, sort_order=order))
    for topic_id in topic_ids or []:
        db.add(TaskTopic(task_id=task.id, topic_id=topic_id))

    await db.commit()
    result = await db.execute(select(Task).where(Task.id == task.id))
    return result.scalar_one()


@pytest.mark.asyncio
async def test_resolve_publish_execution_view_rejects_multiple_videos_without_final_path(
    db_session: AsyncSession,
) -> None:
    video_1 = SimpleNamespace(file_path="videos/video_mv1.mp4")
    video_2 = SimpleNamespace(file_path="videos/video_mv2.mp4")
    task = SimpleNamespace(
        final_video_path=None,
        videos=[video_1, video_2],
        copywritings=[],
        covers=[],
        topics=[],
        audios=[],
    )

    with pytest.raises(PublishabilityError, match="仅支持 1 个最终视频"):
        resolve_publish_execution_view(task)


@pytest.mark.asyncio
async def test_publish_task_marks_failed_for_invalid_direct_publish_combo(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = await _create_account(db_session, "invalid_publish")
    video_1 = await _create_video(db_session, "iv1")
    video_2 = await _create_video(db_session, "iv2")
    task = await _create_raw_task_with_resources(
        db_session,
        account_id=account.id,
        video_ids=[video_1.id, video_2.id],
    )

    get_client = AsyncMock()
    monkeypatch.setattr("services.publish_service.get_dewu_client", get_client)

    service = PublishService(db_session)
    success, message = await service.publish_task(task)

    assert success is False
    assert "仅支持 1 个最终视频" in message
    get_client.assert_not_awaited()

    persisted = await _get_task(db_session, task.id)
    assert persisted.status == "failed"
    assert "仅支持 1 个最终视频" in (persisted.error_msg or "")


@pytest.mark.asyncio
async def test_publish_task_uses_final_video_path_for_composed_task(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = await _create_account(db_session, "final_video")
    video_1 = await _create_video(db_session, "fv1")
    video_2 = await _create_video(db_session, "fv2")
    audio = await _create_audio(db_session, "fv_audio")
    copywriting = await _create_copywriting(db_session, "fv_cw")
    cover = await _create_cover(db_session, "fv_cover")
    topic = await _create_topic(db_session, "fv_topic")
    profile = await _create_profile(db_session, "coze", "coze")

    task = await _create_raw_task_with_resources(
        db_session,
        account_id=account.id,
        video_ids=[video_1.id, video_2.id],
        copywriting_ids=[copywriting.id],
        cover_ids=[cover.id],
        audio_ids=[audio.id],
        topic_ids=[topic.id],
        profile_id=profile.id,
        status="draft",
    )
    task.status = "ready"
    task.final_video_path = "final/final_video.mp4"
    await db_session.commit()

    mock_client = MagicMock()
    mock_client.check_login_status = AsyncMock(return_value=(True, "ok"))
    mock_client.upload_video = AsyncMock(return_value=(True, "ok"))
    monkeypatch.setattr("services.publish_service.get_dewu_client", AsyncMock(return_value=mock_client))
    monkeypatch.setattr(
        "services.publish_service.browser_manager",
        SimpleNamespace(
            get_or_create_context=AsyncMock(return_value=SimpleNamespace(pages=[MagicMock()])),
            new_page=AsyncMock(return_value=MagicMock()),
        ),
    )

    service = PublishService(db_session)
    success, message = await service.publish_task(task)

    assert success is True
    assert message == "发布成功"
    mock_client.upload_video.assert_awaited_once()
    kwargs = mock_client.upload_video.await_args.kwargs
    assert kwargs["video_path"] == "final/final_video.mp4"
    assert kwargs["content"] == copywriting.content
    assert kwargs["cover_path"] == cover.file_path
    assert kwargs["topic"] == topic.name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("auth_state", "denial_reason", "expected_reason"),
    [
        ("revoked", "remote_auth_revoked", "remote_auth_revoked"),
        ("expired", "remote_auth_expired", "remote_auth_expired"),
        (
            "device_mismatch",
            "remote_auth_device_mismatch",
            "remote_auth_device_mismatch",
        ),
    ],
)
async def test_publish_task_marks_failed_with_canonical_auth_reason_after_upload_checkpoint(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
    auth_state: str,
    denial_reason: str,
    expected_reason: str,
) -> None:
    account = await _create_account(db_session, "runtime_auth")
    video = await _create_video(db_session, "runtime_auth")
    task = await _create_raw_task_with_resources(
        db_session,
        account_id=account.id,
        video_ids=[video.id],
        status="ready",
    )

    mock_client = MagicMock()
    mock_client.check_login_status = AsyncMock(return_value=(True, "ok"))
    mock_client.upload_video = AsyncMock(return_value=(True, "ok"))
    monkeypatch.setattr("services.publish_service.get_dewu_client", AsyncMock(return_value=mock_client))
    monkeypatch.setattr(
        "services.publish_service.browser_manager",
        SimpleNamespace(
            get_or_create_context=AsyncMock(return_value=SimpleNamespace(pages=[MagicMock()])),
            new_page=AsyncMock(return_value=MagicMock()),
        ),
    )

    service = PublishService(db_session)
    async def _post_upload_auth_check():
        return LocalAuthSessionSummary(
            auth_state=auth_state,
            remote_user_id="u_123",
            display_name="Alice",
            license_status="active",
            entitlements=["dashboard:view"],
            denial_reason=denial_reason,
            device_id="device-1",
        )

    success, message = await service.publish_task(
        task,
        post_upload_auth_check=_post_upload_auth_check,
    )

    assert success is False
    assert message == expected_reason
    persisted = await _get_task(db_session, task.id)
    assert persisted.status == "failed"
    assert persisted.error_msg == expected_reason
