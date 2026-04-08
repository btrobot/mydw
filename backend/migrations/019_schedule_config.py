"""
迁移 019 — 创建 schedule_config 表，替代 publish_config

变更：
  - 新建 schedule_config 表
  - 若 publish_config 表存在且有数据，迁移 start_hour / end_hour /
    interval_minutes / max_per_account_per_day / shuffle / auto_start
  - 若无数据，插入默认记录

设计原则：幂等 — 表已存在则跳过建表；数据已存在则跳过插入。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 1. 检查 schedule_config 表是否已存在
        existing = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schedule_config'"
            )
        ).fetchall()

        if not existing:
            await conn.exec_driver_sql("""
                CREATE TABLE schedule_config (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name                    VARCHAR(64) DEFAULT 'default',
                    start_hour              INTEGER DEFAULT 9,
                    end_hour                INTEGER DEFAULT 22,
                    interval_minutes        INTEGER DEFAULT 30,
                    max_per_account_per_day INTEGER DEFAULT 5,
                    shuffle                 BOOLEAN DEFAULT 0,
                    auto_start              BOOLEAN DEFAULT 0,
                    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("迁移 019: schedule_config 表已创建")
        else:
            logger.debug("迁移 019: schedule_config 表已存在，跳过建表")
            logger.info("迁移 019 完成")
            return

        # 2. 检查 schedule_config 是否已有数据（幂等保护）
        row_count = (
            await conn.exec_driver_sql("SELECT COUNT(*) FROM schedule_config")
        ).fetchone()[0]

        if row_count > 0:
            logger.debug("迁移 019: schedule_config 已有数据，跳过数据迁移")
            logger.info("迁移 019 完成")
            return

        # 3. 尝试从 publish_config 迁移数据
        publish_config_exists = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='publish_config'"
            )
        ).fetchall()

        if publish_config_exists:
            source_row = (
                await conn.exec_driver_sql(
                    "SELECT start_hour, end_hour, interval_minutes, "
                    "max_per_account_per_day, shuffle, auto_start "
                    "FROM publish_config ORDER BY id LIMIT 1"
                )
            ).fetchone()

            if source_row:
                start_hour, end_hour, interval_minutes, max_per_account_per_day, shuffle, auto_start = source_row
                await conn.exec_driver_sql(
                    "INSERT INTO schedule_config "
                    "(name, start_hour, end_hour, interval_minutes, "
                    "max_per_account_per_day, shuffle, auto_start) "
                    "VALUES ('default', ?, ?, ?, ?, ?, ?)",
                    (start_hour, end_hour, interval_minutes,
                     max_per_account_per_day, int(bool(shuffle)), int(bool(auto_start)))
                )
                logger.info(
                    "迁移 019: 已从 publish_config 迁移数据 "
                    "(start_hour={}, end_hour={}, interval_minutes={}, "
                    "max_per_account_per_day={}, shuffle={}, auto_start={})",
                    start_hour, end_hour, interval_minutes,
                    max_per_account_per_day, shuffle, auto_start
                )
                logger.info("迁移 019 完成")
                return

        # 4. 无可迁移数据，插入默认记录
        await conn.exec_driver_sql(
            "INSERT INTO schedule_config "
            "(name, start_hour, end_hour, interval_minutes, "
            "max_per_account_per_day, shuffle, auto_start) "
            "VALUES ('default', 9, 22, 30, 5, 0, 0)"
        )
        logger.info("迁移 019: 已插入默认 schedule_config 记录")

    logger.info("迁移 019 完成")
