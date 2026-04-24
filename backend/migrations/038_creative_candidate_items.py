"""
Migration 038 - creative candidate items.

Adds creative_candidate_items as the persistent work-level candidate pool.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_CREATIVE_CANDIDATE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS creative_candidate_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
    candidate_type VARCHAR(32) NOT NULL,
    asset_id INTEGER NOT NULL,
    source_kind VARCHAR(32) NOT NULL DEFAULT 'material_library',
    source_product_id INTEGER REFERENCES products(id),
    source_ref VARCHAR(256),
    sort_order INTEGER NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'candidate',
    created_at DATETIME,
    updated_at DATETIME,
    CONSTRAINT uq_creative_candidate_items_creative_type_asset UNIQUE (creative_item_id, candidate_type, asset_id)
)
"""

CREATIVE_CANDIDATE_ITEMS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_candidate_items_creative_item_id ON creative_candidate_items(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_candidate_items_candidate_type ON creative_candidate_items(candidate_type)",
    "CREATE INDEX IF NOT EXISTS ix_creative_candidate_items_asset_id ON creative_candidate_items(asset_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_candidate_items_source_product_id ON creative_candidate_items(source_product_id)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_items = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='creative_items'"
            )
        ).fetchone()
        if creative_items is None:
            logger.info("Migration 038: creative_items table does not exist, skipping")
            return

        await conn.exec_driver_sql(CREATE_CREATIVE_CANDIDATE_ITEMS_TABLE)
        for sql in CREATIVE_CANDIDATE_ITEMS_INDEXES:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 038 complete")
