import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import PublishProfile, Task, Video


async def _seed_ready_snapshot_dependencies(db_session: AsyncSession) -> tuple[PublishProfile, Video]:
    profile = PublishProfile(name="authority-matrix-profile", composition_mode="none", composition_params="{}")
    video = Video(name="authority-matrix-video", file_path="data/videos/authority-matrix.mp4")
    db_session.add_all([profile, video])
    await db_session.commit()
    await db_session.refresh(profile)
    await db_session.refresh(video)
    return profile, video


@pytest.mark.asyncio
async def test_task_execution_state_does_not_become_creative_status_one_to_one(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video = await _seed_ready_snapshot_dependencies(db_session)
    create_response = await client.post(
        "/api/creatives",
        json={"title": "Authority Matrix", "profile_id": profile.id, "video_ids": [video.id]},
    )
    assert create_response.status_code == 201
    creative = create_response.json()

    task = Task(
        status="draft",
        name="Draft Execution Task",
        creative_item_id=creative["id"],
        task_kind="composition",
    )
    db_session.add(task)
    await db_session.commit()

    detail_response = await client.get(f"/api/creatives/{creative['id']}")
    assert detail_response.status_code == 200
    payload = detail_response.json()

    assert payload["latest_task_summary"]["task_status"] == "draft"
    assert payload["status"] == "READY_TO_COMPOSE"


@pytest.mark.asyncio
async def test_work_driven_endpoints_only_allow_aggregate_to_change_business_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video = await _seed_ready_snapshot_dependencies(db_session)
    create_response = await client.post(
        "/api/creatives",
        json={"title": "Authority Matrix 2", "profile_id": profile.id, "video_ids": [video.id]},
    )
    assert create_response.status_code == 201
    creative = create_response.json()

    patch_response = await client.patch(
        f"/api/creatives/{creative['id']}",
        json={"video_ids": []},
    )

    assert patch_response.status_code == 200
    payload = patch_response.json()
    assert payload["status"] == "PENDING_INPUT"
    assert payload["eligibility_status"] == "PENDING_INPUT"
    assert "至少选择 1 个视频" in payload["eligibility_reasons"]
