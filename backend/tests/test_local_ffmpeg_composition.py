from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Account,
    Audio,
    CompositionJob,
    PublishProfile,
    Task,
    TaskAudio,
    TaskVideo,
    Video,
)
from services.composition_service import CompositionService
from services.local_ffmpeg_composition_service import (
    LocalFFmpegCompositionResult,
    LocalFFmpegCompositionService,
)


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"local_ffmpeg_{suffix}",
        account_name=f"Local FFmpeg {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_profile(
    db: AsyncSession,
    suffix: str,
    *,
    composition_params: str | None = None,
) -> PublishProfile:
    profile = PublishProfile(
        name=f"profile_{suffix}",
        composition_mode="local_ffmpeg",
        composition_params=composition_params,
    )
    db.add(profile)
    await db.flush()
    return profile


async def _create_video(db: AsyncSession, suffix: str) -> Video:
    video = Video(name=f"video_{suffix}.mp4", file_path=f"videos/video_{suffix}.mp4")
    db.add(video)
    await db.flush()
    return video


async def _create_audio(db: AsyncSession, suffix: str) -> Audio:
    audio = Audio(name=f"audio_{suffix}.mp3", file_path=f"audios/audio_{suffix}.mp3")
    db.add(audio)
    await db.flush()
    return audio


@pytest.mark.asyncio
async def test_submit_composition_supports_local_ffmpeg_and_writes_back_final_video(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = await _create_account(db_session, "success")
    profile = await _create_profile(
        db_session,
        "success",
        composition_params='{"audio_mix_volume": 0.4, "crf": 21}',
    )
    video = await _create_video(db_session, "success_video")
    audio = await _create_audio(db_session, "success_audio")

    task = Task(account_id=account.id, status="draft", profile_id=profile.id)
    db_session.add(task)
    await db_session.flush()
    db_session.add(TaskVideo(task_id=task.id, video_id=video.id, sort_order=0))
    db_session.add(TaskAudio(task_id=task.id, audio_id=audio.id, sort_order=0))
    await db_session.commit()

    monkeypatch.setattr(
        LocalFFmpegCompositionService,
        "compose",
        AsyncMock(
            return_value=LocalFFmpegCompositionResult(
                output_video_path=f"data/videos/final_{task.id}.mp4",
                output_video_duration=12,
                output_video_size=3456,
            )
        ),
    )

    job = await CompositionService(db_session).submit_composition(task.id)

    persisted_task = await db_session.get(Task, task.id)
    persisted_job = await db_session.get(CompositionJob, job.id)

    assert persisted_job is not None
    assert persisted_job.workflow_type == "local_ffmpeg"
    assert persisted_job.status == "completed"
    assert persisted_job.output_video_path == f"data/videos/final_{task.id}.mp4"
    assert persisted_task is not None
    assert persisted_task.status == "ready"
    assert persisted_task.final_video_path == f"data/videos/final_{task.id}.mp4"
    assert persisted_task.final_video_duration == 12
    assert persisted_task.final_video_size == 3456


@pytest.mark.asyncio
async def test_submit_composition_marks_task_failed_when_local_ffmpeg_execution_fails(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = await _create_account(db_session, "failure")
    profile = await _create_profile(db_session, "failure")
    video = await _create_video(db_session, "failure_video")

    task = Task(account_id=account.id, status="draft", profile_id=profile.id)
    db_session.add(task)
    await db_session.flush()
    db_session.add(TaskVideo(task_id=task.id, video_id=video.id, sort_order=0))
    await db_session.commit()

    monkeypatch.setattr(
        LocalFFmpegCompositionService,
        "compose",
        AsyncMock(side_effect=RuntimeError("ffmpeg 执行失败: mocked crash")),
    )

    with pytest.raises(ValueError, match="mocked crash"):
        await CompositionService(db_session).submit_composition(task.id)

    persisted_task = await db_session.get(Task, task.id)
    assert persisted_task is not None
    assert persisted_task.status == "failed"
    assert persisted_task.failed_at_status == "composing"
    assert "mocked crash" in (persisted_task.error_msg or "")

    persisted_job = await db_session.get(CompositionJob, persisted_task.composition_job_id)
    assert persisted_job is not None
    assert persisted_job.workflow_type == "local_ffmpeg"
    assert persisted_job.status == "failed"
    assert "mocked crash" in (persisted_job.error_msg or "")


def test_local_ffmpeg_runner_mixes_audio_when_source_video_already_has_audio(tmp_path: Path) -> None:
    service = LocalFFmpegCompositionService(output_dir=tmp_path)

    command = service._build_ffmpeg_command(
        source_video_path="videos/source.mp4",
        audio_path="audios/bgm.mp3",
        output_path=tmp_path / "out.mp4",
        source_has_audio=True,
        params={"audio_mix_volume": 0.6},
    )

    assert "-filter_complex" in command
    filter_complex = command[command.index("-filter_complex") + 1]
    assert "[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]" in filter_complex
    assert "volume=0.6" in filter_complex
    assert command.count("-map") == 2
    assert "[aout]" in command


def test_local_ffmpeg_runner_uses_external_audio_directly_when_source_video_has_no_audio(
    tmp_path: Path,
) -> None:
    service = LocalFFmpegCompositionService(output_dir=tmp_path)

    command = service._build_ffmpeg_command(
        source_video_path="videos/source.mp4",
        audio_path="audios/bgm.mp3",
        output_path=tmp_path / "out.mp4",
        source_has_audio=False,
        params={},
    )

    assert "-filter_complex" not in command
    assert command.count("-map") == 2
    assert "1:a:0" in command
    assert "-shortest" in command
