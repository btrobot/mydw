"""
Migration 033 - creative domain model foundation.

Adds creative brief fields onto creative_items and introduces the
creative_input_items table as the additive Phase 1 model layer.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATIVE_ITEM_ADDITIONS = {
    "subject_product_id": "ALTER TABLE creative_items ADD COLUMN subject_product_id INTEGER REFERENCES products(id)",
    "subject_product_name_snapshot": "ALTER TABLE creative_items ADD COLUMN subject_product_name_snapshot VARCHAR(256)",
    "main_copywriting_text": "ALTER TABLE creative_items ADD COLUMN main_copywriting_text TEXT",
    "target_duration_seconds": "ALTER TABLE creative_items ADD COLUMN target_duration_seconds INTEGER",
}

CREATIVE_ITEM_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_items_subject_product_id ON creative_items(subject_product_id)",
]

CREATE_INPUT_ITEMS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS creative_input_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
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

CREATE_INPUT_ITEMS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_input_items_creative_item_id ON creative_input_items(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_input_items_material_type ON creative_input_items(material_type)",
    "CREATE INDEX IF NOT EXISTS ix_creative_input_items_material_id ON creative_input_items(material_id)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_item_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        if not creative_item_columns:
            logger.info("Migration 033: creative_items table does not exist, skipping")
            return

        existing_columns = {column[1] for column in creative_item_columns}

        for column_name, sql in CREATIVE_ITEM_ADDITIONS.items():
            if column_name in existing_columns:
                continue
            await conn.exec_driver_sql(sql)
            logger.info("Migration 033: added creative_items.{}", column_name)

        for sql in CREATIVE_ITEM_INDEXES:
            await conn.exec_driver_sql(sql)

        await conn.exec_driver_sql(CREATE_INPUT_ITEMS_TABLE_SQL)
        for sql in CREATE_INPUT_ITEMS_INDEXES:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 033 complete")
