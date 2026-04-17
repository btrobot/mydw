"""
Migration 029 - Creative Phase C scheduler cutover config.

Adds scheduler cutover control fields to canonical schedule_config truth.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        columns = (await conn.exec_driver_sql("PRAGMA table_info(schedule_config)")).fetchall()
        existing_columns = {col[1] for col in columns}
        additions = {
            "publish_scheduler_mode": "ALTER TABLE schedule_config ADD COLUMN publish_scheduler_mode VARCHAR(16) DEFAULT 'task'",
            "publish_pool_kill_switch": "ALTER TABLE schedule_config ADD COLUMN publish_pool_kill_switch BOOLEAN DEFAULT 0",
            "publish_pool_shadow_read": "ALTER TABLE schedule_config ADD COLUMN publish_pool_shadow_read BOOLEAN DEFAULT 0",
        }

        for column_name, sql in additions.items():
            if column_name not in existing_columns:
                await conn.exec_driver_sql(sql)
                logger.info("Migration 029: added schedule_config.{}", column_name)

        await conn.exec_driver_sql(
            "UPDATE schedule_config SET publish_scheduler_mode='task' WHERE publish_scheduler_mode IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE schedule_config SET publish_pool_kill_switch=0 WHERE publish_pool_kill_switch IS NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE schedule_config SET publish_pool_shadow_read=0 WHERE publish_pool_shadow_read IS NULL"
        )

    logger.info("Migration 029 complete")
