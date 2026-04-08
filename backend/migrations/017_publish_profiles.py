"""
迁移 017 — 创建 publish_profiles 表

变更：
  - 新建 publish_profiles 表 (合成配置档)

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
                "SELECT name FROM sqlite_master WHERE type='table' AND name='publish_profiles'"
            )
        ).fetchall()

        if not tables:
            await conn.exec_driver_sql("""
                CREATE TABLE publish_profiles (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    name                VARCHAR(128) NOT NULL UNIQUE,
                    is_default          BOOLEAN DEFAULT FALSE,
                    composition_mode    VARCHAR(32) DEFAULT 'none',
                    coze_workflow_id    VARCHAR(128),
                    composition_params  TEXT,
                    global_topic_ids    TEXT DEFAULT '[]',
                    auto_retry          BOOLEAN DEFAULT TRUE,
                    max_retry_count     INTEGER DEFAULT 3,
                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_publish_profiles_name ON publish_profiles (name)"
            )
            logger.info("迁移 017: publish_profiles 表已创建")
        else:
            logger.debug("迁移 017: publish_profiles 表已存在，跳过")

    logger.info("迁移 017 完成")
