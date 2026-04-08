"""
迁移 010 — products 表：去掉 name UNIQUE，加 dewu_url UNIQUE partial index

变更：
  - products.name 不再 UNIQUE（允许重名）
  - products.dewu_url 加 UNIQUE partial index（WHERE dewu_url IS NOT NULL）

SQLite 不支持 DROP CONSTRAINT，采用重建表方式。
设计原则：幂等 — 已迁移则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 幂等检查 1：partial index 已存在则跳过
        idx_exists = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='uix_products_dewu_url'"
            )
        ).fetchall()

        if idx_exists:
            logger.debug("迁移 010: uix_products_dewu_url 已存在，跳过")
            logger.info("迁移 010 完成")
            return

        # 幂等检查 2：link 列不存在说明迁移 012 已先执行，products 表已重建
        # 此时直接补建 unique index，跳过重建表逻辑
        col_rows = (
            await conn.exec_driver_sql("PRAGMA table_info(products)")
        ).fetchall()
        col_names = [row[1] for row in col_rows]

        if "link" not in col_names:
            logger.debug("迁移 010: link 列不存在（012 已执行），仅补建 uix_products_dewu_url")
            await conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uix_products_dewu_url "
                "ON products (dewu_url) WHERE dewu_url IS NOT NULL"
            )
            logger.info("迁移 010 完成")
            return

        # 1. 重建 products 表（去掉 name UNIQUE）
        await conn.exec_driver_sql(
            """
            CREATE TABLE products_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        VARCHAR(256) NOT NULL,
                link        VARCHAR(512),
                description TEXT,
                dewu_url    VARCHAR(512),
                image_url   VARCHAR(512),
                created_at  DATETIME,
                updated_at  DATETIME
            )
            """
        )
        await conn.exec_driver_sql(
            """
            INSERT INTO products_new (id, name, link, description, dewu_url, image_url, created_at, updated_at)
            SELECT id, name, link, description, dewu_url, image_url, created_at, updated_at
            FROM products
            """
        )
        await conn.exec_driver_sql("DROP TABLE products")
        await conn.exec_driver_sql("ALTER TABLE products_new RENAME TO products")
        logger.info("迁移 010: products 表已重建（name UNIQUE 已移除）")

        # 2. 重建普通索引（原 ix_products_name）
        await conn.exec_driver_sql(
            "CREATE INDEX ix_products_name ON products (name)"
        )

        # 3. 加 dewu_url UNIQUE partial index
        await conn.exec_driver_sql(
            "CREATE UNIQUE INDEX uix_products_dewu_url ON products (dewu_url) WHERE dewu_url IS NOT NULL"
        )
        logger.info("迁移 010: uix_products_dewu_url partial index 已创建")

    logger.info("迁移 010 完成")
