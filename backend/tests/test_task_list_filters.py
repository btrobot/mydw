from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, CreativeItem, CreativeVersion, PublishProfile, Task


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"task-list-{suffix}",
        account_name=f"Task List {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_profile(db: AsyncSession, suffix: str) -> PublishProfile:
    profile = PublishProfile(
        name=f"profile-{suffix}",
        composition_mode="none",
        is_default=False,
    )
    db.add(profile)
    await db.flush()
    return profile


async def _create_creative_pair(
    db: AsyncSession,
    suffix: str,
) -> tuple[CreativeItem, CreativeVersion]:
    creative = CreativeItem(
        creative_no=f"CR-{suffix}",
        title=f"Creative {suffix}",
        status="PENDING_INPUT",
        latest_version_no=1,
    )
    db.add(creative)
    await db.flush()

    version = CreativeVersion(
        creative_item_id=creative.id,
        version_no=1,
        version_type="generated",
        title=f"Creative {suffix} V1",
    )
    db.add(version)
    await db.flush()
    creative.current_version_id = version.id
    return creative, version


async def _seed_task_list_dataset(db: AsyncSession) -> dict[str, Task]:
    account_a = await _create_account(db, "acct-a")
    account_b = await _create_account(db, "acct-b")
    account_c = await _create_account(db, "acct-c")

    profile_a = await _create_profile(db, "a")
    profile_b = await _create_profile(db, "b")
    profile_c = await _create_profile(db, "c")

    creative_a, version_a = await _create_creative_pair(db, "0001")
    creative_b, version_b = await _create_creative_pair(db, "0002")
    creative_c, version_c = await _create_creative_pair(db, "0003")

    task_a = Task(
        account_id=account_a.id,
        status="failed",
        profile_id=profile_a.id,
        creative_item_id=creative_a.id,
        creative_version_id=version_a.id,
        task_kind="composition",
        batch_id="batch-a",
        failed_at_status="uploading",
        retry_count=3,
        error_msg="upload exploded",
        final_video_path="final/task-a.mp4",
        scheduled_time=datetime(2026, 4, 19, 10, 0, 0),
        publish_time=datetime(2026, 4, 19, 11, 0, 0),
        created_at=datetime(2026, 4, 19, 9, 0, 0),
        updated_at=datetime(2026, 4, 19, 9, 30, 0),
        priority=5,
        name="task-a",
    )
    task_b = Task(
        account_id=account_b.id,
        status="ready",
        profile_id=profile_b.id,
        creative_item_id=creative_b.id,
        creative_version_id=version_b.id,
        task_kind="publish",
        batch_id="batch-b",
        retry_count=0,
        error_msg=None,
        final_video_path=None,
        scheduled_time=datetime(2026, 4, 20, 10, 0, 0),
        publish_time=None,
        created_at=datetime(2026, 4, 18, 8, 0, 0),
        updated_at=datetime(2026, 4, 18, 8, 30, 0),
        priority=2,
        name="task-b",
    )
    task_c = Task(
        account_id=account_c.id,
        status="uploaded",
        profile_id=profile_c.id,
        creative_item_id=creative_c.id,
        creative_version_id=version_c.id,
        task_kind="publish",
        batch_id="batch-c",
        retry_count=1,
        error_msg=None,
        final_video_path="final/task-c.mp4",
        scheduled_time=None,
        publish_time=datetime(2026, 4, 18, 12, 0, 0),
        created_at=datetime(2026, 4, 17, 8, 0, 0),
        updated_at=datetime(2026, 4, 18, 12, 30, 0),
        priority=1,
        name="task-c",
    )

    db.add_all([task_a, task_b, task_c])
    await db.commit()
    return {
        "task_a": task_a,
        "task_b": task_b,
        "task_c": task_c,
        "account_a": account_a,
        "account_b": account_b,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "creative_a": creative_a,
        "version_a": version_a,
    }


async def _get_task_ids(client: AsyncClient, **params) -> list[int]:
    response = await client.get("/api/tasks/", params=params)
    assert response.status_code == 200
    payload = response.json()
    return [item["id"] for item in payload["items"]]


@pytest.mark.asyncio
async def test_list_tasks_supports_exact_filters(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    seeded = await _seed_task_list_dataset(db_session)

    assert await _get_task_ids(client, name="task-a") == [seeded["task_a"].id]
    assert await _get_task_ids(client, name="ask-") == [
        seeded["task_a"].id,
        seeded["task_b"].id,
        seeded["task_c"].id,
    ]
    assert await _get_task_ids(client, status="failed") == [seeded["task_a"].id]
    assert await _get_task_ids(client, account_id=seeded["account_a"].id) == [seeded["task_a"].id]
    assert await _get_task_ids(client, task_kind="composition") == [seeded["task_a"].id]
    assert await _get_task_ids(client, profile_id=seeded["profile_a"].id) == [seeded["task_a"].id]
    assert await _get_task_ids(client, creative_item_id=seeded["creative_a"].id) == [seeded["task_a"].id]
    assert await _get_task_ids(client, creative_version_id=seeded["version_a"].id) == [seeded["task_a"].id]
    assert await _get_task_ids(client, batch_id="batch-a") == [seeded["task_a"].id]
    assert await _get_task_ids(client, failed_at_status="uploading") == [seeded["task_a"].id]


@pytest.mark.asyncio
async def test_list_tasks_supports_range_and_boolean_filters(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    seeded = await _seed_task_list_dataset(db_session)

    assert await _get_task_ids(client, retry_count_min=2) == [seeded["task_a"].id]
    assert await _get_task_ids(client, retry_count_max=0) == [seeded["task_b"].id]
    assert await _get_task_ids(
        client,
        created_from="2026-04-19T08:30:00",
        created_to="2026-04-19T09:30:00",
    ) == [seeded["task_a"].id]
    assert await _get_task_ids(
        client,
        updated_from="2026-04-18T12:00:00",
        updated_to="2026-04-18T13:00:00",
    ) == [seeded["task_c"].id]
    assert await _get_task_ids(
        client,
        scheduled_from="2026-04-19T09:00:00",
        scheduled_to="2026-04-19T11:00:00",
    ) == [seeded["task_a"].id]
    assert await _get_task_ids(
        client,
        publish_from="2026-04-18T11:30:00",
        publish_to="2026-04-18T12:30:00",
    ) == [seeded["task_c"].id]
    assert await _get_task_ids(client, has_error=True) == [seeded["task_a"].id]
    assert set(await _get_task_ids(client, has_error=False)) == {
        seeded["task_b"].id,
        seeded["task_c"].id,
    }
    assert set(await _get_task_ids(client, has_final_video=True)) == {
        seeded["task_a"].id,
        seeded["task_c"].id,
    }
    assert await _get_task_ids(client, has_final_video=False) == [seeded["task_b"].id]


@pytest.mark.asyncio
async def test_list_tasks_supports_combined_filters(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    seeded = await _seed_task_list_dataset(db_session)

    assert await _get_task_ids(
        client,
        name="task-a",
        status="failed",
        task_kind="composition",
        has_error=True,
        retry_count_min=3,
        created_from="2026-04-19T08:30:00",
        created_to="2026-04-19T09:30:00",
    ) == [seeded["task_a"].id]
