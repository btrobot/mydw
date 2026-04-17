from __future__ import annotations

from datetime import datetime
import importlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import (
    Account,
    Copywriting,
    Cover,
    CreativeItem,
    PublishExecutionSnapshot,
    PublishPoolItem,
    PublishProfile,
    ScheduleConfig,
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
from services.publish_service import PublishService


@pytest.mark.asyncio
async def test_migration_029_is_idempotent_and_schedule_config_cutover_columns_exist() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        migration_019 = importlib.import_module("migrations.019_schedule_config")
        migration_029 = importlib.import_module("migrations.029_creative_phase_c_scheduler_cutover")
        await migration_019.run_migration(engine)
        await migration_029.run_migration(engine)
        await migration_029.run_migration(engine)

        async with engine.begin() as conn:
            columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info('schedule_config')")).fetchall()
            }

        assert {"publish_scheduler_mode", "publish_pool_kill_switch", "publish_pool_shadow_read"}.issubset(columns)
    finally:
        await engine.dispose()


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"cutover_{suffix}",
        account_name=f"Cutover {suffix}",
        status="active",
        storage_state="{}",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_publishable_task(
    db: AsyncSession,
    *,
    account: Account,
    suffix: str,
    status: str = "ready",
    priority: int = 0,
    creative_item_id: int | None = None,
    creative_version_id: int | None = None,
    task_kind: str | None = None,
    profile_id: int | None = None,
    final_video_path: str | None = None,
) -> Task:
    video = Video(name=f"video_{suffix}.mp4", file_path=f"videos/video_{suffix}.mp4")
    copywriting = Copywriting(name=f"copy_{suffix}", content=f"文案 {suffix}")
    cover = Cover(name=f"cover_{suffix}", file_path=f"covers/cover_{suffix}.jpg")
    topic = Topic(name=f"topic_{suffix}")
    db.add_all([video, copywriting, cover, topic])
    await db.flush()

    task = Task(
        account_id=account.id,
        status=status,
        priority=priority,
        profile_id=profile_id,
        creative_item_id=creative_item_id,
        creative_version_id=creative_version_id,
        task_kind=task_kind,
        final_video_path=final_video_path,
    )
    db.add(task)
    await db.flush()
    db.add_all(
        [
            TaskVideo(task_id=task.id, video_id=video.id, sort_order=0),
            TaskCopywriting(task_id=task.id, copywriting_id=copywriting.id, sort_order=0),
            TaskCover(task_id=task.id, cover_id=cover.id, sort_order=0),
            TaskTopic(task_id=task.id, topic_id=topic.id),
        ]
    )
    await db.commit()
    return task


async def _seed_pool_candidate(
    db: AsyncSession,
    *,
    suffix: str,
    priority: int = 10,
) -> tuple[PublishPoolItem, Task, Account, PublishProfile]:
    account = await _create_account(db, f"pool_{suffix}")
    profile = PublishProfile(name=f"profile_{suffix}", composition_mode="none", is_default=True)
    creative = CreativeItem(
        creative_no=f"CR-CUTOVER-{suffix}",
        title=f"Cutover {suffix}",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db.add_all([profile, creative])
    await db.flush()

    version = await CreativeVersionService(db).create_initial_version(
        creative,
        title=f"Cutover {suffix} V1",
        package_status="ready",
    )
    creative.status = "WAITING_REVIEW"
    await db.commit()

    source_task = await _create_publishable_task(
        db,
        account=account,
        suffix=f"pool_source_{suffix}",
        status="ready",
        priority=priority,
        creative_item_id=creative.id,
        creative_version_id=version.id,
        task_kind="composition",
        profile_id=profile.id,
        final_video_path=f"final/cutover_{suffix}.mp4",
    )
    await CreativeReviewService(db).approve(
        creative.id,
        version_id=version.id,
        note="approved for cutover publish",
    )
    await db.commit()

    pool_item = (
        await db.execute(
            select(PublishPoolItem).where(PublishPoolItem.creative_item_id == creative.id)
        )
    ).scalar_one()
    return pool_item, source_task, account, profile


async def _set_schedule_config(
    db: AsyncSession,
    *,
    mode: str,
    kill_switch: bool = False,
    shadow_read: bool = False,
    max_per_account_per_day: int = 5,
) -> ScheduleConfig:
    config = (
        await db.execute(select(ScheduleConfig).where(ScheduleConfig.name == "default"))
    ).scalar_one_or_none()
    if config is None:
        config = ScheduleConfig(name="default")
        db.add(config)

    config.start_hour = 0
    config.end_hour = 23
    config.interval_minutes = 30
    config.max_per_account_per_day = max_per_account_per_day
    config.publish_scheduler_mode = mode
    config.publish_pool_kill_switch = kill_switch
    config.publish_pool_shadow_read = shadow_read
    await db.commit()
    return config


@pytest.mark.asyncio
async def test_pool_mode_plans_publish_task_from_pool_not_legacy_ready_task(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    pool_item, _, _, _ = await _seed_pool_candidate(db_session, suffix="pool_mode")
    legacy_account = await _create_account(db_session, "legacy_pool_mode")
    legacy_task = await _create_publishable_task(
        db_session,
        account=legacy_account,
        suffix="legacy_pool_mode",
        status="ready",
        priority=999,
    )
    await _set_schedule_config(db_session, mode="pool")

    service = PublishService(db_session)
    selected = await service.get_next_task()
    report = service.get_last_selection_report()

    assert selected is not None
    assert selected.id != legacy_task.id
    assert selected.task_kind == "publish"
    assert report is not None
    assert report.effective_scheduler_mode == "pool"
    assert report.selected_pool_item_id == pool_item.id

    snapshot = (
        await db_session.execute(
            select(PublishExecutionSnapshot).where(PublishExecutionSnapshot.task_id == selected.id)
        )
    ).scalar_one_or_none()
    assert snapshot is not None
    assert snapshot.pool_item_id == pool_item.id


@pytest.mark.asyncio
async def test_task_mode_keeps_legacy_ready_task_behavior_without_pool_planning(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    await _seed_pool_candidate(db_session, suffix="task_mode")
    legacy_account = await _create_account(db_session, "legacy_task_mode")
    legacy_task = await _create_publishable_task(
        db_session,
        account=legacy_account,
        suffix="legacy_task_mode",
        status="ready",
        priority=999,
    )
    await _set_schedule_config(db_session, mode="task")

    service = PublishService(db_session)
    selected = await service.get_next_task()

    snapshot_count = (
        await db_session.execute(select(PublishExecutionSnapshot))
    ).scalars().all()

    assert selected is not None
    assert selected.id == legacy_task.id
    assert snapshot_count == []


@pytest.mark.asyncio
async def test_kill_switch_forces_task_path_even_when_pool_mode_requested(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    await _seed_pool_candidate(db_session, suffix="kill_switch")
    legacy_account = await _create_account(db_session, "legacy_kill_switch")
    legacy_task = await _create_publishable_task(
        db_session,
        account=legacy_account,
        suffix="legacy_kill_switch",
        status="ready",
        priority=999,
    )
    await _set_schedule_config(db_session, mode="pool", kill_switch=True)

    service = PublishService(db_session)
    selected = await service.get_next_task()
    report = service.get_last_selection_report()

    snapshots = (
        await db_session.execute(select(PublishExecutionSnapshot))
    ).scalars().all()

    assert selected is not None
    assert selected.id == legacy_task.id
    assert report is not None
    assert report.scheduler_mode == "pool"
    assert report.effective_scheduler_mode == "task"
    assert report.publish_pool_kill_switch is True
    assert snapshots == []


@pytest.mark.asyncio
async def test_shadow_read_records_diff_without_planning_in_task_mode(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    pool_item, _, _, _ = await _seed_pool_candidate(db_session, suffix="shadow")
    legacy_account = await _create_account(db_session, "legacy_shadow")
    legacy_task = await _create_publishable_task(
        db_session,
        account=legacy_account,
        suffix="legacy_shadow",
        status="ready",
        priority=999,
    )
    await _set_schedule_config(db_session, mode="task", shadow_read=True)

    service = PublishService(db_session)
    selected = await service.get_next_task()
    report = service.get_last_selection_report()

    snapshots = (
        await db_session.execute(select(PublishExecutionSnapshot))
    ).scalars().all()

    assert selected is not None
    assert selected.id == legacy_task.id
    assert report is not None
    assert report.publish_pool_shadow_read is True
    assert report.shadow_diff is not None
    assert report.shadow_diff.differs is True
    assert report.shadow_diff.pool_item_id == pool_item.id
    assert "selected_task_mismatch" in report.shadow_diff.reasons
    assert "pool_candidate_requires_planning" in report.shadow_diff.reasons
    assert snapshots == []


@pytest.mark.asyncio
async def test_pool_mode_respects_daily_limit_before_planning_publish_task(
    db_session: AsyncSession,
    active_remote_auth_session,
) -> None:
    _, _, account, _ = await _seed_pool_candidate(db_session, suffix="daily_limit")
    uploaded = Task(
        account_id=account.id,
        status="uploaded",
        publish_time=datetime.utcnow(),
    )
    db_session.add(uploaded)
    await db_session.commit()
    await _set_schedule_config(
        db_session,
        mode="pool",
        max_per_account_per_day=1,
    )

    service = PublishService(db_session)
    selected = await service.get_next_task()
    report = service.get_last_selection_report()

    snapshots = (
        await db_session.execute(select(PublishExecutionSnapshot))
    ).scalars().all()

    assert selected is None
    assert report is not None
    assert report.effective_scheduler_mode == "pool"
    assert report.selected_task_id is None
    assert snapshots == []
