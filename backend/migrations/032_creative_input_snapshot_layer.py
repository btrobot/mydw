"""
Migration 032 - independent creative input snapshot carrier layer.

Creates a 1:1 creative_input_snapshots table and backfills it from the
legacy creative_items.input_* columns so the new layer can be rolled out
without breaking the existing creative-first chain.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS creative_input_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creative_item_id INTEGER NOT NULL UNIQUE REFERENCES creative_items(id),
    profile_id INTEGER REFERENCES publish_profiles(id),
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

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_input_snapshots_creative_item_id ON creative_input_snapshots(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_input_snapshots_profile_id ON creative_input_snapshots(profile_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_input_snapshots_snapshot_hash ON creative_input_snapshots(snapshot_hash)",
]

INSERT_MISSING_ROWS_SQL = """
INSERT INTO creative_input_snapshots (
    creative_item_id,
    profile_id,
    video_ids,
    copywriting_ids,
    cover_ids,
    audio_ids,
    topic_ids,
    snapshot_hash,
    created_at,
    updated_at
)
SELECT
    ci.id,
    ci.input_profile_id,
    COALESCE(ci.input_video_ids, '[]'),
    COALESCE(ci.input_copywriting_ids, '[]'),
    COALESCE(ci.input_cover_ids, '[]'),
    COALESCE(ci.input_audio_ids, '[]'),
    COALESCE(ci.input_topic_ids, '[]'),
    ci.input_snapshot_hash,
    ci.created_at,
    ci.updated_at
FROM creative_items ci
WHERE NOT EXISTS (
    SELECT 1
    FROM creative_input_snapshots cis
    WHERE cis.creative_item_id = ci.id
)
"""

SYNC_EXISTING_ROWS_SQL = """
UPDATE creative_input_snapshots
SET
    profile_id = (
        SELECT ci.input_profile_id
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ),
    video_ids = COALESCE((
        SELECT ci.input_video_ids
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ), '[]'),
    copywriting_ids = COALESCE((
        SELECT ci.input_copywriting_ids
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ), '[]'),
    cover_ids = COALESCE((
        SELECT ci.input_cover_ids
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ), '[]'),
    audio_ids = COALESCE((
        SELECT ci.input_audio_ids
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ), '[]'),
    topic_ids = COALESCE((
        SELECT ci.input_topic_ids
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ), '[]'),
    snapshot_hash = (
        SELECT ci.input_snapshot_hash
        FROM creative_items ci
        WHERE ci.id = creative_input_snapshots.creative_item_id
    ),
    created_at = COALESCE(
        created_at,
        (
            SELECT ci.created_at
            FROM creative_items ci
            WHERE ci.id = creative_input_snapshots.creative_item_id
        )
    ),
    updated_at = COALESCE(
        (
            SELECT ci.updated_at
            FROM creative_items ci
            WHERE ci.id = creative_input_snapshots.creative_item_id
        ),
        updated_at,
        created_at
    )
WHERE EXISTS (
    SELECT 1
    FROM creative_items ci
    WHERE ci.id = creative_input_snapshots.creative_item_id
)
"""


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_item_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        if not creative_item_columns:
            logger.info("Migration 032: creative_items table does not exist, skipping")
            return

        existing_columns = {column[1] for column in creative_item_columns}
        required_columns = {
            "input_profile_id",
            "input_video_ids",
            "input_copywriting_ids",
            "input_cover_ids",
            "input_audio_ids",
            "input_topic_ids",
            "input_snapshot_hash",
        }
        if not required_columns.issubset(existing_columns):
            logger.info("Migration 032: creative_items snapshot columns missing, skipping")
            return

        await conn.exec_driver_sql(CREATE_TABLE_SQL)
        for sql in CREATE_INDEXES:
            await conn.exec_driver_sql(sql)

        await conn.exec_driver_sql(INSERT_MISSING_ROWS_SQL)
        await conn.exec_driver_sql(SYNC_EXISTING_ROWS_SQL)

    logger.info("Migration 032 complete")
