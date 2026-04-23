import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Account,
    CreativeVersion,
    PackageRecord,
    PublishExecutionSnapshot,
    PublishPoolItem,
    PublishProfile,
    Task,
    Video,
)
from services.composition_service import CompositionService
from services.creative_review_service import CreativeReviewService
from services.publish_planner_service import PublishPlannerService
from services.task_assembler import TaskAssembler


async def _create_profile_and_video(
    db_session: AsyncSession,
    *,
    suffix: str,
    composition_mode: str,
) -> tuple[PublishProfile, Video]:
    profile = PublishProfile(
        name=f"profile-{suffix}",
        composition_mode=composition_mode,
        composition_params="{}",
        is_default=False,
    )
    video = Video(
        name=f"video-{suffix}.mp4",
        file_path=f"data/videos/video-{suffix}.mp4",
    )
    db_session.add_all([profile, video])
    await db_session.commit()
    await db_session.refresh(profile)
    await db_session.refresh(video)
    return profile, video


async def _create_creative(
    client: AsyncClient,
    *,
    title: str,
    profile_id: int,
    video_id: int,
) -> dict:
    response = await client.post(
        "/api/creatives",
        json={
            "title": title,
            "profile_id": profile_id,
            "input_items": [
                {"material_type": "video", "material_id": video_id},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


class _FakeCozeClient:
    async def upload_file(self, _file_path: str) -> str:
        return "file_fake"

    async def submit_composition(self, _workflow_id: str, _params: dict) -> str:
        return "job_fake"


@pytest.mark.asyncio
async def test_submit_composition_reuses_existing_composing_task(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    active_remote_auth_session,
) -> None:
    profile, video = await _create_profile_and_video(
        db_session,
        suffix="reuse-composing",
        composition_mode="coze",
    )
    profile.coze_workflow_id = "wf-reuse-composing"
    await db_session.commit()
    creative = await _create_creative(
        client,
        title="Reuse Composing",
        profile_id=profile.id,
        video_id=video.id,
    )

    monkeypatch.setattr("services.composition_service.CozeClient", _FakeCozeClient)

    first_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert first_payload["submission_action"] == "created_and_submitted"
    assert first_payload["created_new_task"] is True
    assert first_payload["reused_existing_task"] is False
    assert first_payload["task_status"] == "composing"
    assert first_payload["creative_status"] == "COMPOSING"
    assert first_payload["composition_job_id"] is not None

    second_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["submission_action"] == "reused_composing"
    assert second_payload["created_new_task"] is False
    assert second_payload["reused_existing_task"] is True
    assert second_payload["task_id"] == first_payload["task_id"]
    assert second_payload["composition_job_id"] == first_payload["composition_job_id"]

    tasks = (
        await db_session.execute(
            select(Task).where(Task.creative_item_id == creative["id"]).order_by(Task.id.asc())
        )
    ).scalars().all()
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_submit_composition_reuses_matching_draft_task_before_submitting(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    active_remote_auth_session,
) -> None:
    profile, video = await _create_profile_and_video(
        db_session,
        suffix="reuse-draft",
        composition_mode="coze",
    )
    profile.coze_workflow_id = "wf-reuse-draft"
    await db_session.commit()
    creative = await _create_creative(
        client,
        title="Reuse Draft",
        profile_id=profile.id,
        video_id=video.id,
    )

    draft_task = await TaskAssembler(db_session).assemble(
        account_id=None,
        video_ids=[video.id],
        profile_id=profile.id,
        name="Reuse Draft",
        creative_item_id=creative["id"],
        task_kind="composition",
    )

    monkeypatch.setattr("services.composition_service.CozeClient", _FakeCozeClient)

    response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert response.status_code == 200
    payload = response.json()

    assert payload["submission_action"] == "reused_draft_and_submitted"
    assert payload["created_new_task"] is False
    assert payload["reused_existing_task"] is True
    assert payload["task_id"] == draft_task.id
    assert payload["task_status"] == "composing"

    tasks = (
        await db_session.execute(select(Task).where(Task.creative_item_id == creative["id"]))
    ).scalars().all()
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_submit_composition_creates_new_task_after_previous_failure(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    active_remote_auth_session,
) -> None:
    profile, video = await _create_profile_and_video(
        db_session,
        suffix="retry-after-fail",
        composition_mode="coze",
    )
    profile.coze_workflow_id = "wf-retry-after-fail"
    await db_session.commit()
    creative = await _create_creative(
        client,
        title="Retry After Failure",
        profile_id=profile.id,
        video_id=video.id,
    )

    monkeypatch.setattr("services.composition_service.CozeClient", _FakeCozeClient)

    first_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert first_response.status_code == 200
    first_payload = first_response.json()

    await CompositionService(db_session).handle_failure(
        first_payload["composition_job_id"],
        "renderer timeout",
    )

    second_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert second_response.status_code == 200
    second_payload = second_response.json()

    assert second_payload["submission_action"] == "created_and_submitted"
    assert second_payload["created_new_task"] is True
    assert second_payload["task_id"] != first_payload["task_id"]
    assert second_payload["composition_job_id"] != first_payload["composition_job_id"]

    tasks = (
        await db_session.execute(
            select(Task).where(Task.creative_item_id == creative["id"]).order_by(Task.id.asc())
        )
    ).scalars().all()
    assert [task.status for task in tasks] == ["failed", "composing"]


@pytest.mark.asyncio
async def test_direct_publish_submit_creates_ready_task_and_publish_planner_uses_it_as_source(
    client: AsyncClient,
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    profile, video = await _create_profile_and_video(
        db_session,
        suffix="direct-publish",
        composition_mode="none",
    )
    creative = await _create_creative(
        client,
        title="Direct Publish Creative",
        profile_id=profile.id,
        video_id=video.id,
    )

    submit_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert submit_response.status_code == 200
    payload = submit_response.json()
    assert payload["submission_action"] == "created_ready_task"
    assert payload["task_status"] == "ready"
    assert payload["creative_status"] == "WAITING_REVIEW"
    assert payload["composition_job_id"] is None
    assert payload["current_version_id"] is not None

    repeated_submit_response = await client.post(f"/api/creatives/{creative['id']}/submit-composition")
    assert repeated_submit_response.status_code == 200
    repeated_payload = repeated_submit_response.json()
    assert repeated_payload["submission_action"] == "reused_ready_task"
    assert repeated_payload["task_id"] == payload["task_id"]
    assert repeated_payload["current_version_id"] == payload["current_version_id"]

    version = await db_session.get(CreativeVersion, payload["current_version_id"])
    assert version is not None
    package = (
        await db_session.execute(
            select(PackageRecord).where(PackageRecord.creative_version_id == version.id)
        )
    ).scalar_one()
    assert version.final_video_path == f"data/videos/video-direct-publish.mp4"
    assert version.actual_duration_seconds is None
    assert package.publish_profile_id == profile.id
    assert package.frozen_video_path == f"data/videos/video-direct-publish.mp4"
    assert package.frozen_copywriting_text == ""

    account = Account(
        account_id="publish-source-account",
        account_name="Publish Source Account",
        status="active",
        storage_state="{}",
    )
    db_session.add(account)
    await db_session.flush()

    source_task = await db_session.get(Task, payload["task_id"])
    assert source_task is not None
    source_task.account_id = account.id
    await db_session.commit()

    await CreativeReviewService(db_session).approve(
        creative["id"],
        version_id=payload["current_version_id"],
        note="approved for planner source resolution",
    )
    await db_session.commit()

    pool_item = (
        await db_session.execute(
            select(PublishPoolItem).where(PublishPoolItem.creative_item_id == creative["id"])
        )
    ).scalar_one()

    planning = await PublishPlannerService(db_session).plan_publish_task(pool_item.id)
    snapshot = await db_session.get(PublishExecutionSnapshot, planning.snapshot_id)

    assert planning.source_task_id == payload["task_id"]
    assert snapshot is not None
    assert snapshot.source_task_id == payload["task_id"]
    payload_json = json.loads(snapshot.snapshot_json)
    assert payload_json["publish_package"]["frozen_video_path"] == f"data/videos/video-direct-publish.mp4"
    assert payload_json["execution_view_source"] == "freeze_truth"
