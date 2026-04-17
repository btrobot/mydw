"""
Migration 028 - Creative Phase C publish execution snapshot bridge.

Adds internal pool-lock columns plus the publish_execution_snapshots table used
to freeze publish-planning truth before scheduler cutover.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


SNAPSHOT_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS publish_execution_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pool_item_id INTEGER NOT NULL REFERENCES publish_pool_items(id),
        source_task_id INTEGER NOT NULL REFERENCES tasks(id),
        task_id INTEGER UNIQUE REFERENCES tasks(id),
        creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
        creative_version_id INTEGER NOT NULL REFERENCES creative_versions(id),
        account_id INTEGER NOT NULL REFERENCES accounts(id),
        profile_id INTEGER REFERENCES publish_profiles(id),
        snapshot_json TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_pool_item_id ON publish_execution_snapshots(pool_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_source_task_id ON publish_execution_snapshots(source_task_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_task_id ON publish_execution_snapshots(task_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_creative_item_id ON publish_execution_snapshots(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_creative_version_id ON publish_execution_snapshots(creative_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_account_id ON publish_execution_snapshots(account_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_execution_snapshots_profile_id ON publish_execution_snapshots(profile_id)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        pool_columns = (await conn.exec_driver_sql("PRAGMA table_info(publish_pool_items)")).fetchall()
        existing_pool_columns = {col[1] for col in pool_columns}

        pool_column_sql = {
            "locked_at": "ALTER TABLE publish_pool_items ADD COLUMN locked_at DATETIME",
            "locked_by_task_id": "ALTER TABLE publish_pool_items ADD COLUMN locked_by_task_id INTEGER REFERENCES tasks(id)",
        }

        for column_name, sql in pool_column_sql.items():
            if column_name not in existing_pool_columns:
                await conn.exec_driver_sql(sql)
                logger.info("Migration 028: added publish_pool_items.{}", column_name)

        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_publish_pool_items_locked_at ON publish_pool_items(locked_at)"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_publish_pool_items_locked_by_task_id ON publish_pool_items(locked_by_task_id)"
        )

        for sql in SNAPSHOT_TABLE_STATEMENTS:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 028 complete")
