"""
迁移 006 — PublishConfig 增加 global_topic_ids 列 (SP4-03)

变更：
  publish_config 表新增列：
    - global_topic_ids TEXT DEFAULT '[]'  # JSON数组存储全局话题ID

设计原则：幂等 — PRAGMA table_info 检查列是否已存在。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        col_info = (
            await conn.exec_driver_sql("PRAGMA table_info(publish_config)")
        ).fetchall()
        existing_cols: set[str] = {row[1] for row in col_info}

        if "global_topic_ids" not in existing_cols:
            await conn.exec_driver_sql(
                "ALTER TABLE publish_config ADD COLUMN global_topic_ids TEXT DEFAULT '[]'"
            )
            logger.info("迁移 006: publish_config.global_topic_ids 列已添加")
        else:
            logger.debug("迁移 006: publish_config.global_topic_ids 已存在，跳过")

    logger.info("迁移 006 完成")
