import importlib

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import PublishProfile, Topic, Video


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
