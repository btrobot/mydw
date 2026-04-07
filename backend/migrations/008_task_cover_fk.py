"""
迁移 008 — tasks 表添加 cover_id 外键 (SP6-01)

变更：
  tasks 表新增列：
    - cover_id INTEGER REFERENCES covers(id)

修复 publish_service.py 中 task.cover_path 引用不存在字段的问题。

设计原则：幂等 — 列已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 检查列是否已存在
        columns = (
            await conn.exec_driver_sql("PRAGMA table_info(tasks)")
        ).fetchall()
        column_names = {col[1] for col in columns}

        if "cover_id" in column_names:
            logger.debug("迁移 008: cover_id 列已存在，跳过")
            logger.info("迁移 008 完成")
            return

        await conn.exec_driver_sql(
            "ALTER TABLE tasks ADD COLUMN cover_id INTEGER REFERENCES covers(id)"
        )
        logger.info("迁移 008: tasks.cover_id 列已添加")

    logger.info("迁移 008 完成")
