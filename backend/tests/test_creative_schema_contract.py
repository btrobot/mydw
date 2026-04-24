import importlib

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from models import CreativeCandidateItem, CreativeInputItem, CreativeItem, CreativeProductLink, Product
from schemas import (
    CreativeCandidateStatus,
    CreativeCandidateType,
    CreativeCoverMode,
    CreativeCreateRequest,
    CreativeCopywritingMode,
    CreativeDetailResponse,
    CreativeCurrentCoverAssetType,
    CreativeEligibilityStatus,
    CreativeInputItemResponse,
    CreativeInputMaterialType,
    CreativeItemResponse,
    CreativeProductLinkSourceMode,
    CreativeProductNameMode,
    CreativeStatus,
    CreativeUpdateRequest,
    CreativeVersionSummaryResponse,
    PackageRecordResponse,
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
                for row in (
                    await conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
            task_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(tasks)")).fetchall()
            }
            creative_item_indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_items')")
                ).fetchall()
            }

        assert {"creative_items", "creative_versions", "package_records"}.issubset(tables)
        assert {"creative_item_id", "creative_version_id", "task_kind"}.issubset(task_columns)
        assert "ix_creative_items_creative_no" in creative_item_indexes
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
                for row in (
                    await conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
            indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_input_items')")
                ).fetchall()
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
async def test_migration_035_backfills_missing_input_items_and_retires_snapshot_storage() -> None:
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
                    subject_product_id INTEGER,
                    subject_product_name_snapshot VARCHAR(256),
                    main_copywriting_text TEXT,
                    target_duration_seconds INTEGER,
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
                "CREATE INDEX ix_creative_items_input_profile_id ON creative_items(input_profile_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX ix_creative_items_input_snapshot_hash ON creative_items(input_snapshot_hash)"
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_input_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_item_id INTEGER NOT NULL,
                    material_type VARCHAR(32) NOT NULL,
                    material_id INTEGER NOT NULL,
                    role VARCHAR(64),
                    sequence INTEGER NOT NULL DEFAULT 0,
                    instance_no INTEGER NOT NULL DEFAULT 1,
                    trim_in INTEGER,
                    trim_out INTEGER,
                    slot_duration_seconds INTEGER,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME,
                    updated_at DATETIME,
                    UNIQUE(creative_item_id, sequence)
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
                "CREATE INDEX ix_creative_input_snapshots_creative_item_id ON creative_input_snapshots(creative_item_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX ix_creative_input_snapshots_profile_id ON creative_input_snapshots(profile_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX ix_creative_input_snapshots_snapshot_hash ON creative_input_snapshots(snapshot_hash)"
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_items (
                    id, creative_no, title, input_profile_id, input_video_ids, input_copywriting_ids,
                    input_cover_ids, input_audio_ids, input_topic_ids, input_snapshot_hash
                ) VALUES (
                    1, 'CR-000001', 'legacy row', NULL, '[11,11]', '[21]', '[]', '[]', '[51]', 'legacy-hash'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_input_snapshots (
                    creative_item_id, profile_id, video_ids, copywriting_ids, cover_ids, audio_ids, topic_ids, snapshot_hash
                ) VALUES (
                    1, 9, '[11,11]', '[21]', '[]', '[]', '[51]', 'legacy-hash'
                )
                """
            )

        migration_035 = importlib.import_module("migrations.035_creative_phase4_snapshot_retirement")
        await migration_035.run_migration(engine)
        await migration_035.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (
                    await conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
            creative_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }
            creative_indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_items')")
                ).fetchall()
            }
            backfilled_items = (
                await conn.exec_driver_sql(
                    """
                    SELECT material_type, material_id, sequence, instance_no, enabled
                    FROM creative_input_items
                    WHERE creative_item_id = 1
                    ORDER BY sequence
                    """
                )
            ).fetchall()
            profile_id = (
                await conn.exec_driver_sql(
                    "SELECT input_profile_id FROM creative_items WHERE id = 1"
                )
            ).scalar_one()

        assert "creative_input_snapshots" not in tables
        assert "ix_creative_items_input_snapshot_hash" not in creative_indexes
        assert "input_video_ids" not in creative_columns
        assert "input_copywriting_ids" not in creative_columns
        assert "input_cover_ids" not in creative_columns
        assert "input_audio_ids" not in creative_columns
        assert "input_topic_ids" not in creative_columns
        assert "input_snapshot_hash" not in creative_columns
        assert profile_id == 9
        assert backfilled_items == [
            ("video", 11, 1, 1, 1),
            ("video", 11, 2, 2, 1),
            ("copywriting", 21, 3, 1, 1),
            ("topic", 51, 4, 1, 1),
        ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_036_backfills_current_truth_fields_additively() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
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
                CREATE TABLE covers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    name VARCHAR(256) NOT NULL DEFAULT '',
                    file_path VARCHAR(512) NOT NULL
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE copywritings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL DEFAULT '',
                    content TEXT
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_no VARCHAR(64) NOT NULL,
                    title VARCHAR(256),
                    subject_product_id INTEGER,
                    subject_product_name_snapshot VARCHAR(256),
                    main_copywriting_text TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE creative_input_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_item_id INTEGER NOT NULL,
                    material_type VARCHAR(32) NOT NULL,
                    material_id INTEGER NOT NULL,
                    sequence INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            await conn.exec_driver_sql("INSERT INTO products (id, name) VALUES (1, 'Primary Product')")
            await conn.exec_driver_sql(
                "INSERT INTO covers (id, product_id, name, file_path) VALUES (11, 1, 'Primary Cover', 'data/covers/primary.png')"
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_items (
                    id, creative_no, title, subject_product_id, subject_product_name_snapshot, main_copywriting_text
                ) VALUES (
                    1, 'CR-036-0001', 'Legacy creative', 1, 'Primary Product', 'legacy main copy'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_input_items (
                    creative_item_id, material_type, material_id, sequence
                ) VALUES (
                    1, 'cover', 99, 1
                )
                """
            )

        migration_036 = importlib.import_module("migrations.036_creative_current_truth_explicitization")
        await migration_036.run_migration(engine)
        await migration_036.run_migration(engine)

        async with engine.begin() as conn:
            creative_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }
            creative_indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_items')")
                ).fetchall()
            }
            backfilled_row = (
                await conn.exec_driver_sql(
                    """
                    SELECT
                        current_product_name,
                        product_name_mode,
                        current_cover_asset_type,
                        current_cover_asset_id,
                        cover_mode,
                        current_copywriting_id,
                        current_copywriting_text,
                        copywriting_mode,
                        subject_product_name_snapshot,
                        main_copywriting_text
                    FROM creative_items
                    WHERE id = 1
                    """
                )
            ).fetchone()

        assert {
            "current_product_name",
            "product_name_mode",
            "current_cover_asset_type",
            "current_cover_asset_id",
            "cover_mode",
            "current_copywriting_id",
            "current_copywriting_text",
            "copywriting_mode",
        }.issubset(creative_columns)
        assert "ix_creative_items_current_cover_asset_id" in creative_indexes
        assert "ix_creative_items_current_copywriting_id" in creative_indexes
        assert backfilled_row == (
            "Primary Product",
            "follow_primary_product",
            "cover",
            11,
            "default_from_primary_product",
            None,
            "legacy main copy",
            "manual",
            "Primary Product",
            "legacy main copy",
        )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_037_backfills_creative_product_links_additively() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
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
                CREATE TABLE creative_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_no VARCHAR(64) NOT NULL,
                    title VARCHAR(256),
                    subject_product_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql("INSERT INTO products (id, name) VALUES (1, 'Primary Product')")
            await conn.exec_driver_sql("INSERT INTO products (id, name) VALUES (2, 'Secondary Product')")
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_items (id, creative_no, title, subject_product_id)
                VALUES (1, 'CR-037-0001', 'legacy creative', 2)
                """
            )

        migration_037 = importlib.import_module("migrations.037_creative_product_links")
        await migration_037.run_migration(engine)
        await migration_037.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (
                    await conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
            indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_product_links')")
                ).fetchall()
            }
            product_links = (
                await conn.exec_driver_sql(
                    """
                    SELECT creative_item_id, product_id, sort_order, is_primary, enabled, source_mode
                    FROM creative_product_links
                    ORDER BY creative_item_id, sort_order, id
                    """
                )
            ).fetchall()

        assert "creative_product_links" in tables
        assert "ix_creative_product_links_creative_item_id" in indexes
        assert "ix_creative_product_links_product_id" in indexes
        assert "uq_creative_product_links_primary_per_creative" in indexes
        assert product_links == [
            (1, 2, 1, 1, 1, "import_bootstrap"),
        ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_038_adds_creative_candidate_items_additively() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
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
                CREATE TABLE creative_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creative_no VARCHAR(64) NOT NULL,
                    title VARCHAR(256),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )

        migration_038 = importlib.import_module("migrations.038_creative_candidate_items")
        await migration_038.run_migration(engine)
        await migration_038.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (
                    await conn.exec_driver_sql(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            }
            indexes = {
                row[1]
                for row in (
                    await conn.exec_driver_sql("PRAGMA index_list('creative_candidate_items')")
                ).fetchall()
            }
            table_sql = (
                await conn.exec_driver_sql(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='creative_candidate_items'"
                )
            ).scalar_one()

        assert "creative_candidate_items" in tables
        assert "ix_creative_candidate_items_creative_item_id" in indexes
        assert "ix_creative_candidate_items_candidate_type" in indexes
        assert "ix_creative_candidate_items_asset_id" in indexes
        assert "ix_creative_candidate_items_source_product_id" in indexes
        assert "uq_creative_candidate_items_creative_type_asset" in table_sql
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
        await db_session.execute(select(CreativeItem).where(CreativeItem.id == creative.id))
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


def test_creative_product_link_write_rejects_duplicate_products() -> None:
    with pytest.raises(ValidationError):
        CreativeCreateRequest(
            title="duplicate products",
            product_links=[
                {"product_id": 1, "is_primary": True},
                {"product_id": 1, "is_primary": False},
            ],
        )


def test_creative_product_link_write_rejects_multiple_primaries() -> None:
    with pytest.raises(ValidationError):
        CreativeUpdateRequest(
            product_links=[
                {"product_id": 1, "is_primary": True},
                {"product_id": 2, "is_primary": True},
            ],
        )


def test_creative_candidate_item_write_rejects_duplicate_type_asset_pairs() -> None:
    with pytest.raises(ValidationError):
        CreativeCreateRequest(
            title="duplicate candidates",
            candidate_items=[
                {"candidate_type": "cover", "asset_id": 1},
                {"candidate_type": "cover", "asset_id": 1},
            ],
        )


def test_creative_candidate_item_write_rejects_multiple_adopted_items_per_type() -> None:
    with pytest.raises(ValidationError):
        CreativeUpdateRequest(
            candidate_items=[
                {"candidate_type": "copywriting", "asset_id": 1, "status": "adopted"},
                {"candidate_type": "copywriting", "asset_id": 2, "status": "adopted"},
            ],
        )


def test_creative_candidate_item_write_rejects_adopting_unsupported_media_types() -> None:
    with pytest.raises(ValidationError):
        CreativeCreateRequest(
            title="unsupported adopted candidate",
            candidate_items=[
                {"candidate_type": "video", "asset_id": 1, "status": "adopted"},
            ],
        )


@pytest.mark.asyncio
async def test_creative_product_links_model_supports_single_primary_and_order(db_session) -> None:
    product_a = Product(name="creative-product-a")
    product_b = Product(name="creative-product-b")
    creative = CreativeItem(
        creative_no="CR-SLICE2-0001",
        title="Slice 2 creative",
        status=CreativeStatus.PENDING_INPUT.value,
        latest_version_no=0,
    )
    db_session.add_all([product_a, product_b, creative])
    await db_session.flush()

    db_session.add_all(
        [
            CreativeProductLink(
                creative_item_id=creative.id,
                product_id=product_a.id,
                sort_order=1,
                is_primary=False,
                enabled=True,
                source_mode=CreativeProductLinkSourceMode.MANUAL_ADD.value,
            ),
            CreativeProductLink(
                creative_item_id=creative.id,
                product_id=product_b.id,
                sort_order=2,
                is_primary=True,
                enabled=True,
                source_mode=CreativeProductLinkSourceMode.IMPORT_BOOTSTRAP.value,
            ),
        ]
    )
    await db_session.commit()

    reloaded_links = (
        await db_session.execute(
            select(CreativeProductLink)
            .where(CreativeProductLink.creative_item_id == creative.id)
            .order_by(CreativeProductLink.sort_order.asc(), CreativeProductLink.id.asc())
        )
    ).scalars().all()

    assert [(link.product_id, link.sort_order, link.is_primary) for link in reloaded_links] == [
        (product_a.id, 1, False),
        (product_b.id, 2, True),
    ]


@pytest.mark.asyncio
async def test_creative_candidate_items_model_supports_order_and_status(db_session) -> None:
    creative = CreativeItem(
        creative_no="CR-SLICE3-0001",
        title="Slice 3 creative",
        status=CreativeStatus.PENDING_INPUT.value,
        latest_version_no=0,
    )
    db_session.add(creative)
    await db_session.flush()

    db_session.add_all(
        [
            CreativeCandidateItem(
                creative_item_id=creative.id,
                candidate_type=CreativeCandidateType.COVER.value,
                asset_id=31,
                source_kind="material_library",
                sort_order=2,
                enabled=True,
                status=CreativeCandidateStatus.CANDIDATE.value,
            ),
            CreativeCandidateItem(
                creative_item_id=creative.id,
                candidate_type=CreativeCandidateType.COPYWRITING.value,
                asset_id=21,
                source_kind="llm_generated",
                sort_order=1,
                enabled=True,
                status=CreativeCandidateStatus.ADOPTED.value,
            ),
        ]
    )
    await db_session.commit()

    reloaded_candidates = (
        await db_session.execute(
            select(CreativeCandidateItem)
            .where(CreativeCandidateItem.creative_item_id == creative.id)
            .order_by(CreativeCandidateItem.sort_order.asc(), CreativeCandidateItem.id.asc())
        )
    ).scalars().all()

    assert [(item.candidate_type, item.asset_id, item.status) for item in reloaded_candidates] == [
        (CreativeCandidateType.COPYWRITING.value, 21, CreativeCandidateStatus.ADOPTED.value),
        (CreativeCandidateType.COVER.value, 31, CreativeCandidateStatus.CANDIDATE.value),
    ]


def test_phase_a_task_write_contracts_do_not_expose_task_kind() -> None:
    assert "task_kind" not in TaskCreateRequest.model_fields
    assert "task_kind" not in TaskUpdate.model_fields


def test_work_driven_creative_write_contracts_expose_canonical_inputs_without_snapshot_response_contracts() -> None:
    assert "status" not in CreativeCreateRequest.model_fields
    assert "status" not in CreativeUpdateRequest.model_fields
    assert "profile_id" in CreativeCreateRequest.model_fields
    assert "video_ids" in CreativeCreateRequest.model_fields
    assert "video_ids" in CreativeUpdateRequest.model_fields
    assert "input_items" in CreativeCreateRequest.model_fields
    assert "input_items" in CreativeUpdateRequest.model_fields
    assert "subject_product_id" in CreativeCreateRequest.model_fields
    assert "main_copywriting_text" in CreativeCreateRequest.model_fields
    assert "current_product_name" in CreativeCreateRequest.model_fields
    assert "product_name_mode" in CreativeCreateRequest.model_fields
    assert "current_cover_asset_type" in CreativeCreateRequest.model_fields
    assert "current_cover_asset_id" in CreativeCreateRequest.model_fields
    assert "cover_mode" in CreativeCreateRequest.model_fields
    assert "current_copywriting_id" in CreativeCreateRequest.model_fields
    assert "current_copywriting_text" in CreativeCreateRequest.model_fields
    assert "copywriting_mode" in CreativeCreateRequest.model_fields
    assert "target_duration_seconds" in CreativeCreateRequest.model_fields
    assert "candidate_items" in CreativeCreateRequest.model_fields
    assert "candidate_items" in CreativeUpdateRequest.model_fields
    assert CreativeCreateRequest.model_fields["video_ids"].json_schema_extra == {"deprecated": True}
    assert CreativeUpdateRequest.model_fields["video_ids"].json_schema_extra == {"deprecated": True}

    with pytest.raises(ValidationError):
        CreativeCreateRequest(video_ids=[100])

    with pytest.raises(ValidationError):
        CreativeUpdateRequest(video_ids=[100])

    assert "input_orchestration" in CreativeItemResponse.model_fields
    assert "input_snapshot" not in CreativeItemResponse.model_fields
    assert "candidate_items" in CreativeDetailResponse.model_fields

    request = CreativeCreateRequest(
        profile_id=1,
        subject_product_id=1,
        current_product_name="Current Product",
        product_name_mode=CreativeProductNameMode.MANUAL,
        current_cover_asset_id=10,
        cover_mode=CreativeCoverMode.MANUAL,
        current_copywriting_id=20,
        current_copywriting_text="Current Copy",
        copywriting_mode=CreativeCopywritingMode.MANUAL,
        candidate_items=[
            {"candidate_type": "cover", "asset_id": 10},
        ],
        input_items=[{"material_type": "video", "material_id": 100}],
    )
    assert request.profile_id == 1
    assert len(request.input_items) == 1
    assert len(request.candidate_items) == 1
    assert request.current_cover_asset_type == CreativeCurrentCoverAssetType.COVER
    assert "authoritative writes only accept video/audio" in CreativeCreateRequest.model_fields["input_items"].description
    assert "authoritative writes only accept video/audio" in CreativeUpdateRequest.model_fields["input_items"].description
    assert "Slice 3 persistent" in CreativeCreateRequest.model_fields["candidate_items"].description
    assert "full-carrier compatibility readback" in CreativeDetailResponse.model_fields["input_items"].description

    with pytest.raises(ValidationError):
        CreativeCreateRequest(
            profile_id=1,
            input_items=[{"material_type": "topic", "material_id": 100}],
        )

    response_item = CreativeInputItemResponse(
        material_type=CreativeInputMaterialType.TOPIC,
        material_id=100,
        sequence=1,
        instance_no=1,
    )
    assert response_item.material_type == CreativeInputMaterialType.TOPIC


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
