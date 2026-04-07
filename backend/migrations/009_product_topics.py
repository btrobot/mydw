"""
迁移 009 — 新增 product_topics 关联表

变更：
  新增表 product_topics：
    - id INTEGER PRIMARY KEY
    - product_id INTEGER REFERENCES products(id) ON DELETE CASCADE
    - topic_id INTEGER REFERENCES topics(id)
    - UNIQUE (product_id, topic_id)

设计原则：幂等 — 表已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 检查表是否已存在
        table_info = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='product_topics'"
            )
        ).fetchall()

        if table_info:
            logger.debug("迁移 009: product_topics 表已存在，跳过")
            logger.info("迁移 009 完成")
            return

        await conn.exec_driver_sql(
            """
            CREATE TABLE product_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                topic_id INTEGER NOT NULL REFERENCES topics(id),
                UNIQUE (product_id, topic_id)
            )
            """
        )
        logger.info("迁移 009: product_topics 表已创建")

        await conn.exec_driver_sql(
            "CREATE INDEX ix_product_topics_product_id ON product_topics (product_id)"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX ix_product_topics_topic_id ON product_topics (topic_id)"
        )
        logger.info("迁移 009: product_topics 索引已创建")

    logger.info("迁移 009 完成")
