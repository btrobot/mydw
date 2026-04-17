"""
Migration 027 - Creative Phase C publish pool domain.

Creates the publish_pool_items table used to represent current publishable
Creative versions before scheduler cutover.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS publish_pool_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
        creative_version_id INTEGER NOT NULL UNIQUE REFERENCES creative_versions(id),
        status VARCHAR(32) NOT NULL DEFAULT 'active'
            CHECK (status IN ('active', 'invalidated')),
        invalidation_reason VARCHAR(64),
        invalidated_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CHECK (status != 'invalidated' OR invalidated_at IS NOT NULL)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_publish_pool_items_creative_item_id ON publish_pool_items(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_pool_items_creative_version_id ON publish_pool_items(creative_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_pool_items_status ON publish_pool_items(status)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for sql in CREATE_TABLE_STATEMENTS:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 027 complete")
