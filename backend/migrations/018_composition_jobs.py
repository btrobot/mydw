"""
迁移 018 — 创建 composition_jobs 表

变更：
  - 新建 composition_jobs 表，跟踪视频合成执行过程
  - 一个 Task 可有多个 CompositionJob（重试时创建新记录）

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
                "SELECT name FROM sqlite_master WHERE type='table' AND name='composition_jobs'"
            )
        ).fetchall()

        if not tables:
            await conn.exec_driver_sql("""
                CREATE TABLE composition_jobs (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id             INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    workflow_type       VARCHAR(32),
                    workflow_id         VARCHAR(128),
                    external_job_id     VARCHAR(128),
                    status              VARCHAR(32) DEFAULT 'pending',
                    progress            INTEGER DEFAULT 0,
                    output_video_path   VARCHAR(512),
                    output_video_url    VARCHAR(512),
                    error_msg           TEXT,
                    started_at          DATETIME,
                    completed_at        DATETIME,
                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_composition_jobs_task_id ON composition_jobs (task_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_composition_jobs_status ON composition_jobs (status)"
            )
            logger.info("迁移 018: composition_jobs 表已创建")
        else:
            logger.debug("迁移 018: composition_jobs 表已存在，跳过")

    logger.info("迁移 018 完成")
