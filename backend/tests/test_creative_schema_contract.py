import importlib

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from schemas import (
    CreativeItemResponse,
    CreativeStatus,
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


def test_phase_a_task_write_contracts_do_not_expose_task_kind() -> None:
    assert "task_kind" not in TaskCreateRequest.model_fields
    assert "task_kind" not in TaskUpdate.model_fields


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
    assert version.version_no == 1
    assert package.creative_version_id == 20
