"""
Migration 026 - Creative Phase B composition writeback hints.

Adds Creative-side generation failure hint columns used by PR-B2. The
composition execution truth remains on Task/CompositionJob; these fields only
support workbench/detail visibility and do not encode review conclusions.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        existing_columns = {col[1] for col in columns}

        new_columns = {
            "generation_error_msg": "ALTER TABLE creative_items ADD COLUMN generation_error_msg TEXT",
            "generation_failed_at": "ALTER TABLE creative_items ADD COLUMN generation_failed_at DATETIME",
        }

        added_count = 0
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                await conn.exec_driver_sql(sql)
                logger.info("Migration 026: added creative_items.{}", col_name)
                added_count += 1

        if added_count == 0:
            logger.debug("Migration 026: Creative writeback columns already exist")

    logger.info("Migration 026 complete")
