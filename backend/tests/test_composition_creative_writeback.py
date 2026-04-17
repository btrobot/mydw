import importlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import Account, CheckRecord, CompositionJob, CreativeItem, CreativeVersion, PackageRecord, Task
from services.composition_service import CompositionService
from services.creative_review_service import CreativeReviewService
from services.creative_version_service import CreativeVersionService


@pytest.mark.asyncio
async def test_migration_026_is_idempotent_and_generation_hint_columns_exist() -> None:
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

        migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        migration_026 = importlib.import_module("migrations.026_creative_phase_b_composition_writeback")
        await migration_024.run_migration(engine)
        await migration_026.run_migration(engine)
        await migration_026.run_migration(engine)

        async with engine.begin() as conn:
            creative_item_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }

        assert {"generation_error_msg", "generation_failed_at"}.issubset(creative_item_columns)
    finally:
        await engine.dispose()


async def _seed_composition_creative_task(
    db_session: AsyncSession,
    *,
    creative_no: str = "CR-COMP-0001",
    creative_status: str = "PENDING_INPUT",
    task_status: str = "composing",
) -> tuple[CreativeItem, CreativeVersion, Task, CompositionJob]:
    account = Account(account_id=f"{creative_no}-account", account_name="Composition Creative")
    db_session.add(account)
    await db_session.flush()

    creative = CreativeItem(
        creative_no=creative_no,
        title="Composition Creative",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    initial_version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title="Composition Creative V1",
    )
    creative.status = creative_status

    task = Task(
        account_id=account.id,
        status=task_status,
        name="Composition Creative Task",
        creative_item_id=creative.id,
        creative_version_id=initial_version.id,
        task_kind="composition",
    )
    db_session.add(task)
    await db_session.flush()

    job = CompositionJob(task_id=task.id, workflow_type="none", status="pending")
    db_session.add(job)
    await db_session.flush()
    task.composition_job_id = job.id

    await db_session.commit()
    await db_session.refresh(creative)
    await db_session.refresh(initial_version)
    await db_session.refresh(task)
    await db_session.refresh(job)
    return creative, initial_version, task, job


async def _load_creative(db_session: AsyncSession, creative_id: int) -> CreativeItem:
    result = await db_session.execute(select(CreativeItem).where(CreativeItem.id == creative_id))
    return result.scalar_one()


@pytest.mark.asyncio
async def test_composition_success_creates_and_activates_reviewable_creative_version(
    db_session: AsyncSession,
) -> None:
    creative, initial_version, task, job = await _seed_composition_creative_task(db_session)

    await CompositionService(db_session).handle_success(job.id, {"video_url": None})

    persisted_task = await db_session.get(Task, task.id)
    persisted_job = await db_session.get(CompositionJob, job.id)
    persisted_creative = await _load_creative(db_session, creative.id)
    versions = (
        await db_session.execute(
            select(CreativeVersion)
            .where(CreativeVersion.creative_item_id == creative.id)
            .order_by(CreativeVersion.version_no.asc())
        )
    ).scalars().all()
    packages = (
        await db_session.execute(
            select(PackageRecord).where(PackageRecord.creative_version_id == persisted_creative.current_version_id)
        )
    ).scalars().all()

    assert persisted_job.status == "completed"
    assert persisted_job.progress == 100
    assert persisted_task.status == "ready"
    assert len(versions) == 2
    new_version = versions[-1]
    assert new_version.parent_version_id == initial_version.id
    assert new_version.version_no == 2
    assert persisted_creative.current_version_id == new_version.id
    assert persisted_creative.latest_version_no == 2
    assert persisted_creative.status == "WAITING_REVIEW"
    assert persisted_creative.generation_error_msg is None
    assert persisted_creative.generation_failed_at is None
    assert persisted_task.creative_version_id == new_version.id
    assert len(packages) == 1
    assert packages[0].package_status == "ready"


@pytest.mark.asyncio
async def test_composition_success_writeback_is_not_repeated_for_completed_callback(
    db_session: AsyncSession,
) -> None:
    creative, initial_version, task, job = await _seed_composition_creative_task(
        db_session,
        creative_no="CR-COMP-IDEMPOTENT-0001",
    )

    service = CompositionService(db_session)
    await service.handle_success(job.id, {"video_url": None})
    first_creative = await _load_creative(db_session, creative.id)
    first_version_id = first_creative.current_version_id

    await service.handle_success(job.id, {"video_url": None})

    persisted_task = await db_session.get(Task, task.id)
    persisted_creative = await _load_creative(db_session, creative.id)
    versions = (
        await db_session.execute(select(CreativeVersion).where(CreativeVersion.creative_item_id == creative.id))
    ).scalars().all()

    assert first_version_id is not None
    assert persisted_creative.current_version_id == first_version_id
    assert persisted_creative.latest_version_no == 2
    assert persisted_task.creative_version_id == first_version_id
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_composition_failure_keeps_task_execution_truth_and_writes_creative_hint(
    db_session: AsyncSession,
) -> None:
    creative, initial_version, task, job = await _seed_composition_creative_task(
        db_session,
        creative_no="CR-COMP-FAIL-0001",
        creative_status="WAITING_REVIEW",
    )

    await CompositionService(db_session).handle_failure(job.id, "renderer timeout")

    persisted_task = await db_session.get(Task, task.id)
    persisted_job = await db_session.get(CompositionJob, job.id)
    persisted_creative = await _load_creative(db_session, creative.id)
    versions = (
        await db_session.execute(select(CreativeVersion).where(CreativeVersion.creative_item_id == creative.id))
    ).scalars().all()
    checks = (await db_session.execute(select(CheckRecord))).scalars().all()

    assert persisted_job.status == "failed"
    assert persisted_job.error_msg == "renderer timeout"
    assert persisted_task.status == "failed"
    assert persisted_task.failed_at_status == "composing"
    assert persisted_task.error_msg == "renderer timeout"
    assert persisted_task.creative_version_id == initial_version.id
    assert persisted_creative.status == "WAITING_REVIEW"
    assert persisted_creative.current_version_id == initial_version.id
    assert persisted_creative.generation_error_msg == "renderer timeout"
    assert persisted_creative.generation_failed_at is not None
    assert len(versions) == 1
    assert checks == []


@pytest.mark.asyncio
async def test_composition_failure_does_not_overwrite_existing_review_conclusion(
    db_session: AsyncSession,
) -> None:
    creative, initial_version, task, job = await _seed_composition_creative_task(
        db_session,
        creative_no="CR-COMP-FAIL-REVIEW-0001",
        creative_status="WAITING_REVIEW",
    )
    await CreativeReviewService(db_session).approve(
        creative.id,
        version_id=initial_version.id,
        note="approved before retry failure",
    )
    await db_session.commit()

    await CompositionService(db_session).handle_failure(job.id, "retry failed")

    persisted_creative = await _load_creative(db_session, creative.id)
    checks = (await db_session.execute(select(CheckRecord))).scalars().all()

    assert persisted_creative.status == "APPROVED"
    assert persisted_creative.current_version_id == initial_version.id
    assert persisted_creative.generation_error_msg == "retry failed"
    assert len(checks) == 1
    assert checks[0].conclusion == "APPROVED"


@pytest.mark.asyncio
async def test_legacy_task_without_creative_mapping_keeps_existing_composition_success_behavior(
    db_session: AsyncSession,
) -> None:
    account = Account(account_id="legacy-composition-account", account_name="Legacy Composition")
    db_session.add(account)
    await db_session.flush()
    task = Task(account_id=account.id, status="composing", name="Legacy Composition Task")
    db_session.add(task)
    await db_session.flush()
    job = CompositionJob(task_id=task.id, workflow_type="none", status="pending")
    db_session.add(job)
    await db_session.flush()
    task.composition_job_id = job.id
    await db_session.commit()

    await CompositionService(db_session).handle_success(job.id, {"video_url": None})

    persisted_task = await db_session.get(Task, task.id)
    persisted_job = await db_session.get(CompositionJob, job.id)
    creative_count = (await db_session.execute(select(CreativeItem))).scalars().all()

    assert persisted_job.status == "completed"
    assert persisted_task.status == "ready"
    assert persisted_task.creative_item_id is None
    assert persisted_task.creative_version_id is None
    assert creative_count == []
