"""
迁移 020 — Task 表新增 profile_id、batch_id、failed_at_status 字段

变更：
  - 新增 profile_id (INTEGER) — FK 到 publish_profiles(id)，可为空
  - 新增 batch_id (VARCHAR(64)) — 内部批次追溯标识，非 FK
  - 新增 failed_at_status (VARCHAR(32)) — 失败前状态，用于快速重试

设计原则：幂等 — 字段已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        columns = (
            await conn.exec_driver_sql("PRAGMA table_info(tasks)")
        ).fetchall()

        existing_columns = {col[1] for col in columns}

        new_columns = {
            "profile_id": (
                "ALTER TABLE tasks ADD COLUMN profile_id INTEGER REFERENCES publish_profiles(id)"
            ),
            "batch_id": (
                "ALTER TABLE tasks ADD COLUMN batch_id VARCHAR(64)"
            ),
            "failed_at_status": (
                "ALTER TABLE tasks ADD COLUMN failed_at_status VARCHAR(32)"
            ),
        }

        added_count = 0
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                await conn.exec_driver_sql(sql)
                logger.info("迁移 020: 添加字段 tasks.{}", col_name)
                added_count += 1

        if added_count == 0:
            logger.debug("迁移 020: 所有字段已存在，跳过添加")
        else:
            # 创建 profile_id 索引（加速按 profile 查询任务）
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_tasks_profile_id ON tasks (profile_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_tasks_batch_id ON tasks (batch_id)"
            )
            logger.info("迁移 020: 索引创建完成")

    logger.info("迁移 020 完成")
