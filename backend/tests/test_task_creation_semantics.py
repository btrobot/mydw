"""
Phase 2 / PR3 + Phase 6 / PR1: create / assemble path semantics validation tests.

Phase 6 / PR1 keeps this file focused on authoritative task input rules:
- direct-publish validation is collection-based
- topic multiplicity is allowed at validation time
- topic source resolution is handled elsewhere and must not reintroduce legacy FK semantics here
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Account,
    Copywriting,
    CreativeItem,
    Cover,
    PublishProfile,
    Task,
    TaskCopywriting,
    TaskCover,
    TaskTopic,
    TaskVideo,
    Topic,
    Video,
)
from services.creative_version_service import CreativeVersionService
from services.task_service import TaskService

from services.task_execution_semantics import TaskSemanticsError, validate_task_resource_inputs


def test_validate_task_resource_inputs_rejects_multiple_copywritings_for_direct_publish() -> None:
    with pytest.raises(TaskSemanticsError, match="仅支持 0 或 1 个文案"):
        validate_task_resource_inputs(
            video_ids=[1],
            copywriting_ids=[10, 11],
            composition_mode="none",
        )


def test_validate_task_resource_inputs_rejects_audio_for_direct_publish() -> None:
    with pytest.raises(TaskSemanticsError, match="不支持独立音频输入"):
        validate_task_resource_inputs(
            video_ids=[1],
            audio_ids=[20],
            composition_mode="none",
        )


def test_validate_task_resource_inputs_allows_broader_inputs_for_composition_mode() -> None:
    validate_task_resource_inputs(
        video_ids=[1, 2],
        copywriting_ids=[10, 11],
        cover_ids=[30, 31],
        audio_ids=[20],
        composition_mode="coze",
    )


def test_validate_task_resource_inputs_accepts_local_ffmpeg_v1_combo() -> None:
    validate_task_resource_inputs(
        video_ids=[1],
        copywriting_ids=[10],
        cover_ids=[20],
        audio_ids=[30],
        composition_mode="local_ffmpeg",
    )


def test_validate_task_resource_inputs_rejects_multiple_videos_for_local_ffmpeg() -> None:
    with pytest.raises(TaskSemanticsError, match="local_ffmpeg V1 仅支持 1 个视频输入"):
        validate_task_resource_inputs(
            video_ids=[1, 2],
            composition_mode="local_ffmpeg",
        )


def test_validate_task_resource_inputs_rejects_multiple_audios_for_local_ffmpeg() -> None:
    with pytest.raises(TaskSemanticsError, match="local_ffmpeg V1 仅支持 0 或 1 个音频输入"):
        validate_task_resource_inputs(
            video_ids=[1],
            audio_ids=[20, 21],
            composition_mode="local_ffmpeg",
        )


def test_validate_task_resource_inputs_allows_single_copywriting_and_cover_for_direct_publish() -> None:
    validate_task_resource_inputs(
        video_ids=[1],
        copywriting_ids=[10],
        cover_ids=[20],
        composition_mode="none",
    )


@pytest.mark.asyncio
async def test_clone_as_publish_task_projects_publish_shell_from_freeze_truth(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    account = Account(account_id="clone_publish_account", account_name="Clone Publish", status="active", storage_state="{}")
    profile = PublishProfile(name="clone_publish_profile", composition_mode="none")
    video = Video(name="clone_publish_video.mp4", file_path="videos/clone_publish_video.mp4")
    copywriting = Copywriting(name="clone_publish_copy", content="clone publish content")
    cover = Cover(name="clone_publish_cover", file_path="covers/clone_publish_cover.jpg")
    topic = Topic(name="clone_publish_topic")
    creative = CreativeItem(
        creative_no="CR-CLONE-PUBLISH-0001",
        title="Clone Publish Creative",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add_all([account, profile, video, copywriting, cover, topic, creative])
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(creative, title="Clone Publish V1")
    source_task = Task(
        account_id=account.id,
        status="ready",
        name="Clone Publish Source",
        profile_id=profile.id,
        creative_item_id=creative.id,
        creative_version_id=version.id,
        task_kind="composition",
        final_video_path="final/clone_publish.mp4",
    )
    db_session.add(source_task)
    await db_session.flush()
    db_session.add_all(
        [
            TaskVideo(task_id=source_task.id, video_id=video.id, sort_order=0),
            TaskCopywriting(task_id=source_task.id, copywriting_id=copywriting.id, sort_order=0),
            TaskCover(task_id=source_task.id, cover_id=cover.id, sort_order=0),
            TaskTopic(task_id=source_task.id, topic_id=topic.id),
        ]
    )
    await db_session.commit()

    cloned_task = await TaskService(db_session).clone_as_publish_task(
        source_task,
        creative_item_id=creative.id,
        creative_version_id=version.id,
        profile_id=profile.id,
        account_id=account.id,
        frozen_video_path="final/frozen_clone_publish.mp4",
        frozen_duration_seconds=33,
        batch_id="publish-pool:test",
    )

    assert cloned_task.task_kind == "publish"
    assert cloned_task.status == "ready"
    assert cloned_task.profile_id == profile.id
    assert cloned_task.creative_item_id == creative.id
    assert cloned_task.creative_version_id == version.id
    assert cloned_task.final_video_path == "final/frozen_clone_publish.mp4"
    assert cloned_task.final_video_duration == 33
    assert [item.id for item in cloned_task.videos] == []
    assert [item.id for item in cloned_task.copywritings] == []
    assert [item.id for item in cloned_task.covers] == []
    assert [item.id for item in cloned_task.topics] == []
