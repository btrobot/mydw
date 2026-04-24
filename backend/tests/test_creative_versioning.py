import importlib
import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import Account, CreativeItem, CreativeVersion, PackageRecord, PublishPoolItem
from schemas import CreativeStatus, CreativeUpdateRequest
from services.creative_review_service import CreativeReviewService
from services.creative_service import CreativeService
from services.creative_version_service import CreativeVersionService


@pytest.mark.asyncio
async def test_migration_025_is_idempotent_and_review_invariant_columns_exist() -> None:
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
        migration_025 = importlib.import_module("migrations.025_creative_phase_b_review_invariants")
        await migration_024.run_migration(engine)
        await migration_025.run_migration(engine)
        await migration_025.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            creative_version_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_versions)")).fetchall()
            }
            check_record_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('check_records')")).fetchall()
            }

        assert "check_records" in tables
        assert "parent_version_id" in creative_version_columns
        assert "ix_check_records_creative_version_id" in check_record_indexes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_initial_version_sets_current_pointer_and_package_record(
    db_session: AsyncSession,
) -> None:
    creative = CreativeItem(
        creative_no="CR-VERSION-0001",
        title="Creative Versioning",
        status="PENDING_INPUT",
        latest_version_no=0,
        subject_product_name_snapshot="Initial Product Name",
        main_copywriting_text="Initial Copywriting Text",
        target_duration_seconds=30,
    )
    db_session.add(creative)
    await db_session.flush()

    version = await CreativeVersionService(db_session).create_initial_version(
        creative,
        title="Creative Versioning V1",
    )
    await db_session.commit()

    result = await db_session.execute(
        select(CreativeVersion).where(CreativeVersion.id == version.id)
    )
    persisted_version = result.scalar_one()

    assert creative.current_version_id == version.id
    assert creative.latest_version_no == 1
    assert version.parent_version_id is None
    detail = await CreativeService(db_session).get_creative_detail(creative.id)
    assert persisted_version.id == version.id
    assert detail is not None
    assert detail.current_version is not None
    assert detail.current_version.package_record_id is not None
    assert detail.current_version.final_product_name == "Initial Product Name"
    assert detail.current_version.final_copywriting_text == "Initial Copywriting Text"
    assert detail.current_version.package_record is not None
    assert detail.current_version.package_record.frozen_product_name == "Initial Product Name"
    assert detail.current_version.package_record.frozen_copywriting_text == "Initial Copywriting Text"
    assert detail.current_version.package_record.frozen_duration_seconds == 30


@pytest.mark.asyncio
async def test_migration_034_is_idempotent_and_freeze_contract_columns_exist() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_item_id INTEGER NOT NULL,
                    parent_version_id INTEGER,
                    version_no INTEGER NOT NULL DEFAULT 1,
                    version_type VARCHAR(32) NOT NULL DEFAULT 'generated',
                    title VARCHAR(256),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE package_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_version_id INTEGER NOT NULL,
                    package_status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    manifest_json TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )

        migration_034 = importlib.import_module("migrations.034_creative_phase3_freeze_contract")
        await migration_034.run_migration(engine)
        await migration_034.run_migration(engine)

        async with engine.begin() as conn:
            version_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_versions)")).fetchall()
            }
            package_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(package_records)")).fetchall()
            }
            package_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('package_records')")).fetchall()
            }

        assert {
            "actual_duration_seconds",
            "final_video_path",
            "final_product_name",
            "final_copywriting_text",
        }.issubset(version_columns)
        assert {
            "publish_profile_id",
            "frozen_video_path",
            "frozen_cover_path",
            "frozen_duration_seconds",
            "frozen_product_name",
            "frozen_copywriting_text",
        }.issubset(package_columns)
        assert "ix_package_records_publish_profile_id" in package_indexes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_next_version_invalidates_previous_approval_summary(
    db_session: AsyncSession,
) -> None:
    account = Account(account_id="creative-version-account", account_name="Creative Version")
    db_session.add(account)
    await db_session.flush()

    creative = CreativeItem(
        creative_no="CR-VERSION-0002",
        title="Creative Versioning Approval",
        status="PENDING_INPUT",
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    version_service = CreativeVersionService(db_session)
    review_service = CreativeReviewService(db_session)

    v1 = await version_service.create_initial_version(creative, title="V1")
    creative.status = "WAITING_REVIEW"
    await db_session.commit()

    await review_service.approve(creative.id, version_id=v1.id, note="ship it")
    await db_session.commit()

    v2 = await version_service.create_next_version(creative, title="V2")
    await db_session.commit()

    detail = await CreativeService(db_session).get_creative_detail(creative.id)
    pool_items = (
        await db_session.execute(
            select(PublishPoolItem).where(PublishPoolItem.creative_item_id == creative.id)
        )
    ).scalars().all()

    assert v2.parent_version_id == v1.id
    assert detail is not None
    assert detail.current_version_id == v2.id
    assert detail.status == CreativeStatus.WAITING_REVIEW
    assert detail.review_summary is not None
    assert detail.review_summary.current_check is None
    assert [version.id for version in detail.versions] == [v2.id, v1.id]
    assert detail.versions[1].latest_check is not None
    assert detail.versions[1].latest_check.conclusion.value == "APPROVED"
    assert detail.versions[1].is_current is False
    assert len(pool_items) == 1
    assert pool_items[0].creative_version_id == v1.id
    assert pool_items[0].status == "invalidated"
    assert pool_items[0].invalidation_reason == "superseded_by_new_version"


@pytest.mark.asyncio
async def test_update_creative_does_not_mutate_approved_version_freeze_snapshot(
    db_session: AsyncSession,
) -> None:
    creative = CreativeItem(
        creative_no="CR-VERSION-0003",
        title="Creative Version Freeze Guard",
        status="PENDING_INPUT",
        latest_version_no=0,
        subject_product_name_snapshot="Approved Product",
        main_copywriting_text="Approved Copy",
        target_duration_seconds=30,
    )
    db_session.add(creative)
    await db_session.flush()

    version_service = CreativeVersionService(db_session)
    review_service = CreativeReviewService(db_session)

    version = await version_service.create_initial_version(creative, title="Approved V1")
    creative.status = "WAITING_REVIEW"
    await db_session.commit()

    await review_service.approve(creative.id, version_id=version.id, note="freeze it")
    await db_session.commit()

    await CreativeService(db_session).update_creative(
        creative.id,
        CreativeUpdateRequest(
            subject_product_name_snapshot="Edited Product Definition",
            main_copywriting_text="Edited Copy Definition",
            target_duration_seconds=45,
        ),
    )

    persisted_version = await db_session.get(CreativeVersion, version.id)
    assert persisted_version is not None
    package_record = (
        await db_session.execute(
            select(PackageRecord).where(PackageRecord.creative_version_id == version.id)
        )
    ).scalars().one()
    persisted_creative = await db_session.get(CreativeItem, creative.id)
    assert persisted_creative is not None

    assert persisted_creative.subject_product_name_snapshot == "Edited Product Definition"
    assert persisted_creative.main_copywriting_text == "Edited Copy Definition"
    assert persisted_creative.target_duration_seconds == 45
    assert persisted_version.final_product_name == "Approved Product"
    assert persisted_version.final_copywriting_text == "Approved Copy"
    assert persisted_version.actual_duration_seconds is None
    assert persisted_version.final_video_path is None
    assert package_record.frozen_product_name == "Approved Product"
    assert package_record.frozen_copywriting_text == "Approved Copy"
    assert package_record.frozen_duration_seconds == 30
    manifest = json.loads(package_record.manifest_json or "{}")
    assert manifest["current_product_name"] == "Approved Product"
    assert manifest["current_copywriting"]["text"] == "Approved Copy"
