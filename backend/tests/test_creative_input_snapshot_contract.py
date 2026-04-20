import importlib

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import CreativeInputSnapshot, CreativeItem, PublishProfile, Topic, Video


@pytest.mark.asyncio
async def test_migration_031_is_idempotent_and_creative_snapshot_columns_exist() -> None:
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
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL,
                    composition_mode VARCHAR(32),
                    composition_params TEXT
                )
                """
            )

        migration = importlib.import_module("migrations.031_creative_workdriven_phase1")
        await migration.run_migration(engine)
        await migration.run_migration(engine)

        async with engine.begin() as conn:
            creative_item_columns = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
            }
            creative_item_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('creative_items')")).fetchall()
            }

        assert {
            "input_profile_id",
            "input_video_ids",
            "input_copywriting_ids",
            "input_cover_ids",
            "input_audio_ids",
            "input_topic_ids",
            "input_snapshot_hash",
        }.issubset(creative_item_columns)
        assert "ix_creative_items_input_snapshot_hash" in creative_item_indexes
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_032_is_idempotent_and_backfills_independent_snapshot_rows() -> None:
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
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL
                )
                """
            )
            await conn.exec_driver_sql("INSERT INTO publish_profiles(id, name) VALUES (1, 'snapshot-profile')")
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_items (
                    id, creative_no, title, input_profile_id, input_video_ids, input_copywriting_ids,
                    input_cover_ids, input_audio_ids, input_topic_ids, input_snapshot_hash
                ) VALUES (
                    1, 'CR-000001', 'snapshot row', 1, '[11]', '[22]', '[33]', '[44]', '[55]', 'hash-001'
                )
                """
            )

        migration = importlib.import_module("migrations.032_creative_input_snapshot_layer")
        await migration.run_migration(engine)
        await migration.run_migration(engine)

        async with engine.begin() as conn:
            tables = {
                row[0]
                for row in (await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )).fetchall()
            }
            snapshot_indexes = {
                row[1]
                for row in (await conn.exec_driver_sql("PRAGMA index_list('creative_input_snapshots')")).fetchall()
            }
            rows = (
                await conn.exec_driver_sql(
                    """
                    SELECT creative_item_id, profile_id, video_ids, copywriting_ids, cover_ids, audio_ids, topic_ids, snapshot_hash
                    FROM creative_input_snapshots
                    ORDER BY creative_item_id
                    """
                )
            ).fetchall()

        assert "creative_input_snapshots" in tables
        assert "ix_creative_input_snapshots_snapshot_hash" in snapshot_indexes
        assert rows == [(1, 1, "[11]", "[22]", "[33]", "[44]", "[55]", "hash-001")]
    finally:
        await engine.dispose()


async def _seed_snapshot_dependencies(
    db_session: AsyncSession,
    *,
    profile_name: str,
) -> tuple[PublishProfile, Video, Topic]:
    profile = PublishProfile(name=profile_name, composition_mode="none", composition_params="{}")
    video = Video(name=f"{profile_name}-video", file_path=f"data/videos/{profile_name}.mp4")
    topic = Topic(name=f"{profile_name}-topic")
    db_session.add_all([profile, video, topic])
    await db_session.commit()
    await db_session.refresh(profile)
    await db_session.refresh(video)
    await db_session.refresh(topic)
    return profile, video, topic


@pytest.mark.asyncio
async def test_input_snapshot_contract_deduplicates_ids_and_keeps_hash_stable(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, topic = await _seed_snapshot_dependencies(
        db_session,
        profile_name="snapshot-contract-profile",
    )

    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Snapshot Contract",
            "profile_id": profile.id,
            "video_ids": [video.id, video.id],
            "topic_ids": [topic.id, topic.id],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    first_hash = created["input_snapshot"]["snapshot_hash"]
    assert created["input_snapshot"]["video_ids"] == [video.id]
    assert created["input_snapshot"]["topic_ids"] == [topic.id]

    patch_response = await client.patch(
        f"/api/creatives/{created['id']}",
        json={"video_ids": [video.id, video.id], "topic_ids": [topic.id, topic.id]},
    )

    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["input_snapshot"]["snapshot_hash"] == first_hash
    assert patched["status"] == "READY_TO_COMPOSE"


@pytest.mark.asyncio
async def test_input_snapshot_dual_write_keeps_new_and_legacy_carriers_in_sync(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, topic = await _seed_snapshot_dependencies(
        db_session,
        profile_name="snapshot-dual-write-profile",
    )

    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Dual Write Snapshot",
            "profile_id": profile.id,
            "video_ids": [video.id],
            "topic_ids": [topic.id],
        },
    )
    assert create_response.status_code == 201
    creative_id = create_response.json()["id"]

    patch_response = await client.patch(
        f"/api/creatives/{creative_id}",
        json={"video_ids": [video.id, video.id], "topic_ids": [topic.id]},
    )
    assert patch_response.status_code == 200
    payload = patch_response.json()

    creative = await db_session.get(CreativeItem, creative_id)
    assert creative is not None
    snapshot_row = (
        await db_session.execute(
            select(CreativeInputSnapshot).where(CreativeInputSnapshot.creative_item_id == creative_id)
        )
    ).scalar_one()

    assert creative.input_profile_id == snapshot_row.profile_id == profile.id
    assert creative.input_video_ids == snapshot_row.video_ids == f"[{video.id}]"
    assert creative.input_topic_ids == snapshot_row.topic_ids == f"[{topic.id}]"
    assert creative.input_snapshot_hash == snapshot_row.snapshot_hash == payload["input_snapshot"]["snapshot_hash"]


@pytest.mark.asyncio
async def test_input_snapshot_read_falls_back_to_legacy_and_next_write_recreates_snapshot_row(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    profile, video, topic = await _seed_snapshot_dependencies(
        db_session,
        profile_name="snapshot-rollback-profile",
    )

    create_response = await client.post(
        "/api/creatives",
        json={
            "title": "Rollback Snapshot",
            "profile_id": profile.id,
            "video_ids": [video.id],
            "topic_ids": [topic.id],
        },
    )
    assert create_response.status_code == 201
    creative_id = create_response.json()["id"]

    await db_session.execute(
        delete(CreativeInputSnapshot).where(CreativeInputSnapshot.creative_item_id == creative_id)
    )
    await db_session.commit()

    detail_response = await client.get(f"/api/creatives/{creative_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["input_snapshot"]["profile_id"] == profile.id
    assert detail_payload["input_snapshot"]["video_ids"] == [video.id]
    assert detail_payload["input_snapshot"]["topic_ids"] == [topic.id]

    patch_response = await client.patch(
        f"/api/creatives/{creative_id}",
        json={"title": "Rollback Snapshot Recreated"},
    )
    assert patch_response.status_code == 200

    recreated = (
        await db_session.execute(
            select(CreativeInputSnapshot).where(CreativeInputSnapshot.creative_item_id == creative_id)
        )
    ).scalar_one()
    assert recreated.profile_id == profile.id
    assert recreated.video_ids == f"[{video.id}]"
    assert recreated.topic_ids == f"[{topic.id}]"
