"""
迁移 007 — task_topics 表添加唯一约束 (SP5-01)

变更：
  task_topics 表新增唯一索引：
    - uq_task_topic (task_id, topic_id)

设计原则：幂等 — 先去重再建索引，索引已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 检查索引是否已存在
        index_info = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='uq_task_topic'"
            )
        ).fetchall()

        if index_info:
            logger.debug("迁移 007: uq_task_topic 索引已存在，跳过")
            logger.info("迁移 007 完成")
            return

        # 先去重：保留每组 (task_id, topic_id) 中 id 最小的行
        await conn.exec_driver_sql(
            """
            DELETE FROM task_topics
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM task_topics
                GROUP BY task_id, topic_id
            )
            """
        )
        logger.info("迁移 007: task_topics 重复行已清理")

        # 建唯一索引
        await conn.exec_driver_sql(
            "CREATE UNIQUE INDEX uq_task_topic ON task_topics (task_id, topic_id)"
        )
        logger.info("迁移 007: uq_task_topic 唯一索引已创建")

    logger.info("迁移 007 完成")
