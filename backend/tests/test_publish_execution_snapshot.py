import importlib
import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from models import (
    Account,
    Copywriting,
    Cover,
    CreativeItem,
    PublishExecutionSnapshot,
    PublishPoolItem,
    PublishProfile,
    Task,
    TaskCopywriting,
    TaskCover,
    TaskTopic,
    TaskVideo,
    Topic,
    Video,
)
from services.creative_review_service import CreativeReviewService
from services.creative_version_service import CreativeVersionService
from services.publish_planner_service import PublishPlannerService
from services.task_service import TaskService


@pytest.mark.asyncio
async def test_migration_028_is_idempotent_and_snapshot_contract_exists() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    status VARCHAR(32) DEFAULT 'draft'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id VARCHAR(64) NOT NULL,
                    account_name VARCHAR(128) NOT NULL
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL
                )
                """
            )

        migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        migration_025 = importlib.import_module("migrations.025_creative_phase_b_review_invariants")
        migration_027 = importlib.import_module("migrations.027_creative_phase_c_publish_pool")
        migration_028 = importlib.import_module("migrations.028_creative_phase_c_publish_execution_snapshot")
        await migration_024.run_migration(engine)
        await migration_025.run_migration(engine)
        await migration_027.run_migration(engine)
        await migration_028.run_migration(engine)
        await migration_028.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            pool_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info('publish_pool_items')")).fetchall()
            }
            snapshot_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('publish_execution_snapshots')")).fetchall()
            }

        assert "publish_execution_snapshots" in tables
        assert {"locked_at", "locked_by_task_id"}.issubset(pool_columns)
        assert "ix_publish_execution_snapshots_task_id" in snapshot_indexes
    finally:
        await engine.dispose()


async def _seed_publishable_pool_candidate(
    db_session: AsyncSession,
    *,
    suffix: str = "0001",
) -> tuple[PublishPoolItem, Task, Account, PublishProfile, CreativeItem]:
    account = Account(
        account_id=f"publish-plan-{suffix}",
        account_name=f"Publish Planner {suffix}",
        status="active",
        storage_state="{}",
    )
    profile = PublishProfile(
        name=f"profile-{suffix}",
        is_default=True,
        composition_mode="none",
    )
    video = Video(name=f"video-{suffix}.mp4", file_path=f"videos/video-{suffix}.mp4")
    copywriting = Copywriting(name=f"copy-{suffix}", content=f"文案 {suffix}")
    cover = Cover(name=f"cover-{suffix}", file_path=f"covers/cover-{suffix}.jpg")
    topic = Topic(name=f"topic-{suffix}")
    creative = CreativeItem(
        creative_no=f"CR-PLAN-{suffix}",
        title=f"Creative {suffix}",
        status="PENDING_INPUT",
        latest_version_no=0,
    )

    db_session.add_all([account, profile, video, copywriting, cover, topic, creative])
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title=f"Creative {suffix} V1",
        package_status="ready",
    )
    creative.status = "WAITING_REVIEW"

    source_task = Task(
        account_id=account.id,
        status="ready",
        name=f"Source Publish Task {suffix}",
        profile_id=profile.id,
        creative_item_id=creative.id,
        creative_version_id=version.id,
        task_kind="composition",
        final_video_path=f"final/final-{suffix}.mp4",
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

    await CreativeReviewService(db_session).approve(creative.id, version_id=version.id, note="approved for publish")
    await db_session.commit()

    pool_item = (
        await db_session.execute(
            select(PublishPoolItem)
            .options(selectinload(PublishPoolItem.creative_item))
            .where(PublishPoolItem.creative_item_id == creative.id)
        )
    ).scalar_one()
    return pool_item, source_task, account, profile, creative


@pytest.mark.asyncio
async def test_plan_publish_task_creates_snapshot_and_binds_publish_task(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    pool_item, source_task, account, profile, creative = await _seed_publishable_pool_candidate(
        db_session,
        suffix="bind",
    )

    result = await PublishPlannerService(db_session).plan_publish_task(pool_item.id)

    snapshot = await db_session.get(PublishExecutionSnapshot, result.snapshot_id)
    planned_task = await TaskService(db_session).get_task(result.task_id)
    refreshed_pool_item = await db_session.get(PublishPoolItem, pool_item.id)

    assert snapshot is not None
    assert snapshot.pool_item_id == pool_item.id
    assert snapshot.source_task_id == source_task.id
    assert snapshot.task_id == result.task_id
    assert snapshot.account_id == account.id
    assert snapshot.profile_id == profile.id

    assert planned_task is not None
    assert planned_task.task_kind == "publish"
    assert planned_task.creative_item_id == creative.id
    assert planned_task.creative_version_id == pool_item.creative_version_id
    assert planned_task.profile_id == profile.id
    assert planned_task.status == "ready"
    assert planned_task.final_video_path == source_task.final_video_path
    assert planned_task.batch_id == f"publish-pool:{pool_item.id}"

    payload = json.loads(snapshot.snapshot_json)
    assert payload["creative_item"]["id"] == creative.id
    assert payload["creative_version"]["id"] == pool_item.creative_version_id
    assert payload["account"]["id"] == account.id
    assert payload["profile"]["id"] == profile.id
    assert payload["execution_view"]["video_path"] == source_task.final_video_path
    assert payload["source_task"]["id"] == source_task.id

    assert refreshed_pool_item is not None
    assert refreshed_pool_item.locked_at is not None
    assert refreshed_pool_item.locked_by_task_id == result.task_id


@pytest.mark.asyncio
async def test_planning_failure_rolls_back_pool_lock_and_snapshot(
    db_session: AsyncSession,
    active_remote_auth_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pool_item, _, _, _, _ = await _seed_publishable_pool_candidate(
        db_session,
        suffix="rollback",
    )
    pool_item_id = pool_item.id

    async def _boom(*args, **kwargs):
        raise RuntimeError("planner clone failed")

    monkeypatch.setattr(TaskService, "clone_as_publish_task", _boom)

    with pytest.raises(RuntimeError, match="planner clone failed"):
        await PublishPlannerService(db_session).plan_publish_task(pool_item_id)

    refreshed_pool_item = await db_session.get(PublishPoolItem, pool_item_id)
    snapshots = (
        await db_session.execute(
            select(PublishExecutionSnapshot).where(PublishExecutionSnapshot.pool_item_id == pool_item_id)
        )
    ).scalars().all()
    publish_tasks = (
        await db_session.execute(select(Task).where(Task.task_kind == "publish"))
    ).scalars().all()

    assert refreshed_pool_item is not None
    assert refreshed_pool_item.locked_at is None
    assert refreshed_pool_item.locked_by_task_id is None
    assert snapshots == []
    assert publish_tasks == []
