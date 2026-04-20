"""
Migration 031 - work-driven creative flow phase 1 snapshot fields.

Adds pre-compose snapshot carrier fields to creative_items so a creative can
exist before its first generated version.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATIVE_ITEM_ADDITIONS = {
    "input_profile_id": "ALTER TABLE creative_items ADD COLUMN input_profile_id INTEGER REFERENCES publish_profiles(id)",
    "input_video_ids": "ALTER TABLE creative_items ADD COLUMN input_video_ids TEXT DEFAULT '[]' NOT NULL",
    "input_copywriting_ids": "ALTER TABLE creative_items ADD COLUMN input_copywriting_ids TEXT DEFAULT '[]' NOT NULL",
    "input_cover_ids": "ALTER TABLE creative_items ADD COLUMN input_cover_ids TEXT DEFAULT '[]' NOT NULL",
    "input_audio_ids": "ALTER TABLE creative_items ADD COLUMN input_audio_ids TEXT DEFAULT '[]' NOT NULL",
    "input_topic_ids": "ALTER TABLE creative_items ADD COLUMN input_topic_ids TEXT DEFAULT '[]' NOT NULL",
    "input_snapshot_hash": "ALTER TABLE creative_items ADD COLUMN input_snapshot_hash VARCHAR(64)",
}

CREATIVE_ITEM_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_items_input_profile_id ON creative_items(input_profile_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_input_snapshot_hash ON creative_items(input_snapshot_hash)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_item_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        if not creative_item_columns:
            logger.info("Migration 031: creative_items table does not exist, skipping")
            return

        existing_columns = {column[1] for column in creative_item_columns}

        for column_name, sql in CREATIVE_ITEM_ADDITIONS.items():
            if column_name in existing_columns:
                continue
            await conn.exec_driver_sql(sql)
            logger.info("Migration 031: added creative_items.{}", column_name)

        await conn.exec_driver_sql(
            "UPDATE creative_items SET input_video_ids='[]' WHERE input_video_ids IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE creative_items SET input_copywriting_ids='[]' WHERE input_copywriting_ids IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE creative_items SET input_cover_ids='[]' WHERE input_cover_ids IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE creative_items SET input_audio_ids='[]' WHERE input_audio_ids IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE creative_items SET input_topic_ids='[]' WHERE input_topic_ids IS NULL"
        )

        for sql in CREATIVE_ITEM_INDEXES:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 031 complete")
