"""
迁移 015 — 创建 topic_groups 表

变更：
  - 新建 topic_groups 表 (id, name, topic_ids, created_at, updated_at)

设计原则：幂等 — 表已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        tables = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='topic_groups'"
            )
        ).fetchall()

        if not tables:
            await conn.exec_driver_sql("""
                CREATE TABLE topic_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL UNIQUE,
                    topic_ids TEXT NOT NULL DEFAULT '[]',
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_topic_groups_name ON topic_groups (name)"
            )
            logger.info("迁移 015: topic_groups 表已创建")
        else:
            logger.debug("迁移 015: topic_groups 表已存在，跳过")

    logger.info("迁移 015 完成")
