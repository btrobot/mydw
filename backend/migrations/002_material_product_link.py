"""
迁移 002 — 素材关联商品

新增字段：
  - materials.product_id  INTEGER (FK -> products.id)

设计原则：幂等 — 重复执行不报错。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


_COLUMNS: list[tuple[str, str]] = [
    ("product_id", "INTEGER REFERENCES products(id)"),
]

_TABLE = "materials"


async def run_migration(engine: AsyncEngine) -> None:
    """幂等地为 materials 表添加 product_id 列。"""
    async with engine.begin() as conn:
        # 检查 materials 表是否存在
        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='materials'"
        )
        if not result.fetchone():
            logger.info("迁移 002: materials 表不存在，跳过")
            return

        # 获取现有列
        rows = await conn.exec_driver_sql(f"PRAGMA table_info({_TABLE})")
        existing = {r[1] for r in rows}

        for col_name, col_ddl in _COLUMNS:
            if col_name in existing:
                logger.debug("迁移 002: 列 {}.{} 已存在，跳过", _TABLE, col_name)
                continue
            stmt = f"ALTER TABLE {_TABLE} ADD COLUMN {col_name} {col_ddl}"
            await conn.exec_driver_sql(stmt)
            logger.info("迁移 002: 已添加列 {}.{}", _TABLE, col_name)

    logger.info("迁移 002 完成")
