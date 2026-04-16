"""
迁移 024 — Creative Phase A 最小骨架
变更：
  - 新建 creative_items 表
  - 新建 creative_versions 表
  - 新建 package_records 表
  - 为 tasks 增加 creative_item_id / creative_version_id / task_kind
设计原则：幂等；表/列已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS creative_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creative_no VARCHAR(64) NOT NULL UNIQUE,
        title VARCHAR(256),
        status VARCHAR(32) NOT NULL DEFAULT 'PENDING_INPUT',
        current_version_id INTEGER REFERENCES creative_versions(id),
        latest_version_no INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_creative_items_creative_no ON creative_items(creative_no)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_status ON creative_items(status)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_current_version_id ON creative_items(current_version_id)",
    """
    CREATE TABLE IF NOT EXISTS creative_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
        version_no INTEGER NOT NULL DEFAULT 1,
        version_type VARCHAR(32) NOT NULL DEFAULT 'generated',
        title VARCHAR(256),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(creative_item_id, version_no)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_creative_versions_creative_item_id ON creative_versions(creative_item_id)",
    """
    CREATE TABLE IF NOT EXISTS package_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creative_version_id INTEGER NOT NULL UNIQUE REFERENCES creative_versions(id),
        package_status VARCHAR(32) NOT NULL DEFAULT 'pending',
        manifest_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_package_records_creative_version_id ON package_records(creative_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_package_records_package_status ON package_records(package_status)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for sql in CREATE_TABLE_STATEMENTS:
            await conn.exec_driver_sql(sql)

        columns = (
            await conn.exec_driver_sql("PRAGMA table_info(tasks)")
        ).fetchall()
        existing_columns = {col[1] for col in columns}

        new_columns = {
            "creative_item_id": (
                "ALTER TABLE tasks ADD COLUMN creative_item_id INTEGER REFERENCES creative_items(id)"
            ),
            "creative_version_id": (
                "ALTER TABLE tasks ADD COLUMN creative_version_id INTEGER REFERENCES creative_versions(id)"
            ),
            "task_kind": (
                "ALTER TABLE tasks ADD COLUMN task_kind VARCHAR(32)"
            ),
        }

        added_count = 0
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                await conn.exec_driver_sql(sql)
                logger.info("迁移 024: 添加字段 tasks.{}", col_name)
                added_count += 1

        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_tasks_creative_item_id ON tasks (creative_item_id)"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_tasks_creative_version_id ON tasks (creative_version_id)"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_tasks_task_kind ON tasks (task_kind)"
        )

        if added_count == 0:
            logger.debug("迁移 024: Creative Phase A 字段已存在，跳过新增列")

    logger.info("迁移 024 完成")
