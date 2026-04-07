"""
迁移 003 — 商品表增强 (SP1-06)

新增字段：
  - products.dewu_url   VARCHAR(512)  — 得物商品页 URL
  - products.image_url  VARCHAR(512)  — 商品图片

设计原则：幂等 — 重复执行不报错。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


_TABLE = "products"

_COLUMNS: list[tuple[str, str]] = [
    ("dewu_url",  "VARCHAR(512)"),
    ("image_url", "VARCHAR(512)"),
]


async def run_migration(engine: AsyncEngine) -> None:
    """幂等地为 products 表添加 dewu_url 和 image_url 列。"""
    async with engine.begin() as conn:
        rows = await conn.exec_driver_sql(f"PRAGMA table_info({_TABLE})")
        existing = {r[1] for r in rows}

        for col_name, col_ddl in _COLUMNS:
            if col_name in existing:
                logger.debug("迁移 003: 列 {}.{} 已存在，跳过", _TABLE, col_name)
                continue
            stmt = f"ALTER TABLE {_TABLE} ADD COLUMN {col_name} {col_ddl}"
            await conn.exec_driver_sql(stmt)
            logger.info("迁移 003: 已添加列 {}.{}", _TABLE, col_name)

    logger.info("迁移 003 完成")
