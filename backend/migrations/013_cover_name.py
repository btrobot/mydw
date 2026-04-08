"""
迁移 013 — covers 表加 name 列

变更：
  - covers 表加 name VARCHAR(256) NOT NULL DEFAULT ''

设计原则：幂等 — 列已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        rows = (
            await conn.exec_driver_sql("PRAGMA table_info(covers)")
        ).fetchall()
        col_names = [row[1] for row in rows]

        if "name" not in col_names:
            await conn.exec_driver_sql(
                "ALTER TABLE covers ADD COLUMN name VARCHAR(256) NOT NULL DEFAULT ''"
            )
            logger.info("迁移 013: covers.name 列已添加")
        else:
            logger.debug("迁移 013: covers.name 列已存在，跳过")

    logger.info("迁移 013 完成")
