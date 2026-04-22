import importlib

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from models import CreativeInputItem, CreativeItem, Product
from schemas import (
    CreativeEligibilityStatus,
    CreativeItemResponse,
    CreativeStatus,
    CreativeVersionSummaryResponse,
    PackageRecordResponse,
    CreativeCreateRequest,
    CreativeUpdateRequest,
    TaskCreateRequest,
    TaskKind,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


@pytest.mark.asyncio
async def test_migration_024_is_idempotent_and_creative_columns_exist() -> None:
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

        migration = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        await migration.run_migration(engine)
        await migration.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            task_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(tasks)")).fetchall()
            }
            creative_item_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('creative_items')")).fetchall()
            }

        assert {"creative_items", "creative_versions", "package_records"}.issubset(tables)
        assert {"creative_item_id", "creative_version_id", "task_kind"}.issubset(task_columns)
        assert "ix_creative_items_creative_no" in creative_item_indexes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_031_creative_snapshot_columns_are_additive() -> None:
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
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL
                )
                """
            )

        migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        migration_031 = importlib.import_module("migrations.031_creative_workdriven_phase1")
        await migration_024.run_migration(engine)
        await migration_031.run_migration(engine)
        await migration_031.run_migration(engine)

        async with engine.begin() as conn:
            creative_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }

        assert "input_profile_id" in creative_columns
        assert "input_snapshot_hash" in creative_columns
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_032_creative_input_snapshot_layer_is_additive() -> None:
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
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL
                )
                """
            )

        migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
        migration_031 = importlib.import_module("migrations.031_creative_workdriven_phase1")
        migration_032 = importlib.import_module("migrations.032_creative_input_snapshot_layer")
        await migration_024.run_migration(engine)
        await migration_031.run_migration(engine)
        await migration_032.run_migration(engine)
        await migration_032.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }

        assert "creative_input_snapshots" in tables
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_033_creative_domain_model_foundation_is_additive() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_no VARCHAR(64) NOT NULL,
                    title VARCHAR(256),
                    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_INPUT',
                    current_version_id INTEGER,
                    latest_version_no INTEGER NOT NULL DEFAULT 0,
                    generation_error_msg TEXT,
                    generation_failed_at DATETIME,
                    input_profile_id INTEGER,
                    input_video_ids TEXT DEFAULT '[]' NOT NULL,
                    input_copywriting_ids TEXT DEFAULT '[]' NOT NULL,
                    input_cover_ids TEXT DEFAULT '[]' NOT NULL,
                    input_audio_ids TEXT DEFAULT '[]' NOT NULL,
                    input_topic_ids TEXT DEFAULT '[]' NOT NULL,
                    input_snapshot_hash VARCHAR(64),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL
                )
                """
            )

        migration_033 = importlib.import_module("migrations.033_creative_domain_model_foundation")
        await migration_033.run_migration(engine)
        await migration_033.run_migration(engine)

        async with engine.begin() as conn:
            creative_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('creative_input_items')")).fetchall()
            }

        assert {
            "subject_product_id",
            "subject_product_name_snapshot",
            "main_copywriting_text",
            "target_duration_seconds",
        }.issubset(creative_columns)
        assert "creative_input_items" in tables
        assert "ix_creative_input_items_creative_item_id" in indexes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_033_preserves_legacy_snapshot_carriers_without_backfilling_authoritative_items() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_no VARCHAR(64) NOT NULL,
                    title VARCHAR(256),
                    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_INPUT',
                    current_version_id INTEGER,
                    latest_version_no INTEGER NOT NULL DEFAULT 0,
                    generation_error_msg TEXT,
                    generation_failed_at DATETIME,
                    input_profile_id INTEGER,
                    input_video_ids TEXT DEFAULT '[]' NOT NULL,
                    input_copywriting_ids TEXT DEFAULT '[]' NOT NULL,
                    input_cover_ids TEXT DEFAULT '[]' NOT NULL,
                    input_audio_ids TEXT DEFAULT '[]' NOT NULL,
                    input_topic_ids TEXT DEFAULT '[]' NOT NULL,
                    input_snapshot_hash VARCHAR(64),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_input_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_item_id INTEGER NOT NULL UNIQUE,
                    profile_id INTEGER,
                    video_ids TEXT NOT NULL DEFAULT '[]',
                    copywriting_ids TEXT NOT NULL DEFAULT '[]',
                    cover_ids TEXT NOT NULL DEFAULT '[]',
                    audio_ids TEXT NOT NULL DEFAULT '[]',
                    topic_ids TEXT NOT NULL DEFAULT '[]',
                    snapshot_hash VARCHAR(64),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_items (
                    id, creative_no, title, input_profile_id, input_video_ids, input_copywriting_ids,
                    input_cover_ids, input_audio_ids, input_topic_ids, input_snapshot_hash
                ) VALUES (
                    1, 'CR-MIGRATION-033', 'legacy creative', 8, '[101,101]', '[]', '[]', '[]', '[301]', 'legacy-hash-033'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_input_snapshots (
                    creative_item_id, profile_id, video_ids, copywriting_ids, cover_ids, audio_ids, topic_ids, snapshot_hash
                ) VALUES (
                    1, 8, '[101,101]', '[]', '[]', '[]', '[301]', 'legacy-hash-033'
                )
                """
            )

        migration_033 = importlib.import_module("migrations.033_creative_domain_model_foundation")
        await migration_033.run_migration(engine)
        await migration_033.run_migration(engine)

        async with engine.begin() as conn:
            creative_row = (
                await conn.exec_driver_sql(
                    """
                    SELECT input_profile_id, input_video_ids, input_topic_ids, input_snapshot_hash
                    FROM creative_items
                    WHERE id = 1
                    """
                )
            ).fetchone()
            snapshot_row = (
                await conn.exec_driver_sql(
                    """
                    SELECT profile_id, video_ids, topic_ids, snapshot_hash
                    FROM creative_input_snapshots
                    WHERE creative_item_id = 1
                    """
                )
            ).fetchone()
            input_item_count = (
                await conn.execute(text("SELECT COUNT(*) FROM creative_input_items WHERE creative_item_id = 1"))
            ).scalar_one()

        assert creative_row == (8, "[101,101]", "[301]", "legacy-hash-033")
        assert snapshot_row == (8, "[101,101]", "[301]", "legacy-hash-033")
        assert input_item_count == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_creative_input_items_preserve_duplicate_order_and_trim(db_session) -> None:
    product = Product(name="creative_phase1_contract_product")
    creative = CreativeItem(
        creative_no="CR-PHASE1-PR1-0001",
        title="Phase 1 PR1 Creative",
        status=CreativeStatus.PENDING_INPUT.value,
        latest_version_no=0,
        subject_product=product,
        subject_product_name_snapshot="Phase 1 Product Snapshot",
        main_copywriting_text="Phase 1 Copywriting Snapshot",
        target_duration_seconds=45,
    )
    db_session.add_all([product, creative])
    await db_session.flush()

    db_session.add_all(
        [
            CreativeInputItem(
                creative_item_id=creative.id,
                material_type="video",
                material_id=101,
                role="primary",
                sequence=1,
                instance_no=1,
                trim_in=0,
                trim_out=15,
                enabled=True,
            ),
            CreativeInputItem(
                creative_item_id=creative.id,
                material_type="video",
                material_id=101,
                role="ending",
                sequence=2,
                instance_no=2,
                trim_in=20,
                trim_out=35,
                enabled=True,
            ),
        ]
    )
    await db_session.commit()

    reloaded = (
        await db_session.execute(
            select(CreativeItem).where(CreativeItem.id == creative.id)
        )
    ).scalar_one()
    input_items = (
        await db_session.execute(
            select(CreativeInputItem)
            .where(CreativeInputItem.creative_item_id == creative.id)
            .order_by(CreativeInputItem.sequence.asc(), CreativeInputItem.id.asc())
        )
    ).scalars().all()

    assert reloaded.subject_product_id == product.id
    assert reloaded.subject_product_name_snapshot == "Phase 1 Product Snapshot"
    assert reloaded.main_copywriting_text == "Phase 1 Copywriting Snapshot"
    assert reloaded.target_duration_seconds == 45
    assert [item.material_id for item in input_items] == [101, 101]
    assert [item.sequence for item in input_items] == [1, 2]
    assert [item.role for item in input_items] == ["primary", "ending"]
    assert [(item.trim_in, item.trim_out) for item in input_items] == [(0, 15), (20, 35)]


def test_phase_a_task_write_contracts_do_not_expose_task_kind() -> None:
    assert "task_kind" not in TaskCreateRequest.model_fields
    assert "task_kind" not in TaskUpdate.model_fields


def test_work_driven_creative_write_contracts_expose_phase2_canonical_inputs_and_deprecated_legacy_projection_fields() -> None:
    assert "status" not in CreativeCreateRequest.model_fields
    assert "status" not in CreativeUpdateRequest.model_fields
    assert "profile_id" in CreativeCreateRequest.model_fields
    assert "video_ids" in CreativeCreateRequest.model_fields
    assert "video_ids" in CreativeUpdateRequest.model_fields
    assert "input_items" in CreativeCreateRequest.model_fields
    assert "input_items" in CreativeUpdateRequest.model_fields
    assert "subject_product_id" in CreativeCreateRequest.model_fields
    assert "main_copywriting_text" in CreativeCreateRequest.model_fields
    assert "target_duration_seconds" in CreativeCreateRequest.model_fields
    assert CreativeCreateRequest.model_fields["video_ids"].json_schema_extra == {"deprecated": True}
    assert CreativeUpdateRequest.model_fields["video_ids"].json_schema_extra == {"deprecated": True}

    with pytest.raises(ValidationError):
        CreativeCreateRequest(video_ids=[100])

    with pytest.raises(ValidationError):
        CreativeUpdateRequest(video_ids=[100])

    request = CreativeCreateRequest(
        profile_id=1,
        input_items=[{"material_type": "video", "material_id": 100}],
    )
    assert request.profile_id == 1
    assert len(request.input_items) == 1


def test_phase_a_response_contracts_are_instantiable() -> None:
    task = TaskResponse(
        id=1,
        account_id=2,
        creative_item_id=10,
        creative_version_id=20,
        task_kind=TaskKind.COMPOSITION,
        video_ids=[100],
        copywriting_ids=[],
        cover_ids=[],
        audio_ids=[],
        topic_ids=[],
        status=TaskStatus.DRAFT,
        priority=1,
        created_at="2026-04-17T00:00:00",
        updated_at="2026-04-17T00:00:00",
    )
    creative = CreativeItemResponse(
        id=10,
        creative_no="CR-0001",
        title="Creative Title",
        status=CreativeStatus.PENDING_INPUT,
        current_version_id=20,
        latest_version_no=1,
        generation_error_msg="last render failed",
        generation_failed_at="2026-04-17T00:00:00",
        eligibility_status=CreativeEligibilityStatus.PENDING_INPUT,
        eligibility_reasons=["请选择合成配置"],
        created_at="2026-04-17T00:00:00",
        updated_at="2026-04-17T00:00:00",
    )
    version = CreativeVersionSummaryResponse(
        id=20,
        creative_item_id=10,
        version_no=1,
        version_type="generated",
        title="V1",
        created_at="2026-04-17T00:00:00",
        updated_at="2026-04-17T00:00:00",
    )
    package = PackageRecordResponse(
        id=30,
        creative_version_id=20,
        package_status="pending",
        manifest_json=None,
        created_at="2026-04-17T00:00:00",
        updated_at="2026-04-17T00:00:00",
    )

    assert task.task_kind == TaskKind.COMPOSITION
    assert creative.current_version_id == 20
    assert creative.generation_error_msg == "last render failed"
    assert creative.eligibility_status == CreativeEligibilityStatus.PENDING_INPUT
    assert version.version_no == 1
    assert package.creative_version_id == 20
