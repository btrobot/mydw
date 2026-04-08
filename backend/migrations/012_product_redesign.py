"""
迁移 012 — 商品表重构（Product Redesign）

变更：
  - products 表加 parse_status VARCHAR(20) DEFAULT 'pending'
  - products 表加 video_count INT DEFAULT 0
  - products 表加 copywriting_count INT DEFAULT 0
  - products 表加 cover_count INT DEFAULT 0
  - products 表加 topic_count INT DEFAULT 0
  - products 表删 link、description、image_url 列（SQLite 需重建表）
  - covers 表加 product_id INTEGER FK（nullable）

设计原则：幂等 — 列已存在则跳过；重建表前检查列是否已删除。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:

        # ── products 表：加新列 ──────────────────────────────────────────
        products_cols_rows = (
            await conn.exec_driver_sql("PRAGMA table_info(products)")
        ).fetchall()
        products_col_names = [row[1] for row in products_cols_rows]

        new_columns = [
            ("parse_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("video_count", "INTEGER DEFAULT 0"),
            ("copywriting_count", "INTEGER DEFAULT 0"),
            ("cover_count", "INTEGER DEFAULT 0"),
            ("topic_count", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_def in new_columns:
            if col_name not in products_col_names:
                await conn.exec_driver_sql(
                    f"ALTER TABLE products ADD COLUMN {col_name} {col_def}"
                )
                logger.info("迁移 012: products.{} 列已添加", col_name)
            else:
                logger.debug("迁移 012: products.{} 列已存在，跳过", col_name)

        # ── products 表：删 link / description / image_url（重建表）──────
        # 重新读取最新列信息（上面可能刚加了列）
        products_cols_rows = (
            await conn.exec_driver_sql("PRAGMA table_info(products)")
        ).fetchall()
        products_col_names = [row[1] for row in products_cols_rows]

        cols_to_drop = {"link", "description", "image_url"}
        needs_rebuild = bool(cols_to_drop & set(products_col_names))

        if needs_rebuild:
            logger.info("迁移 012: 重建 products 表以删除废弃列: {}", cols_to_drop & set(products_col_names))

            # 保留的列（按原顺序过滤）
            keep_cols = [row[1] for row in products_cols_rows if row[1] not in cols_to_drop]
            cols_csv = ", ".join(keep_cols)

            await conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
            await conn.exec_driver_sql(
                "CREATE TABLE products_new AS SELECT " + cols_csv + " FROM products WHERE 0"
            )
            # 补全列定义（CREATE TABLE AS 不保留约束，需手动重建）
            await conn.exec_driver_sql("DROP TABLE products_new")

            # 手动建新表（保留所有约束）
            await conn.exec_driver_sql("""
                CREATE TABLE IF NOT EXISTS products_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL,
                    dewu_url VARCHAR(512),
                    parse_status VARCHAR(20) DEFAULT 'pending',
                    video_count INTEGER DEFAULT 0,
                    copywriting_count INTEGER DEFAULT 0,
                    cover_count INTEGER DEFAULT 0,
                    topic_count INTEGER DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)

            # 迁移数据（只复制两表都有的列）
            src_cols = [c for c in keep_cols if c in [
                "id", "name", "dewu_url", "parse_status",
                "video_count", "copywriting_count", "cover_count", "topic_count",
                "created_at", "updated_at",
            ]]
            src_csv = ", ".join(src_cols)
            await conn.exec_driver_sql(
                f"INSERT INTO products_new ({src_csv}) SELECT {src_csv} FROM products"
            )

            await conn.exec_driver_sql("DROP TABLE products")
            await conn.exec_driver_sql("ALTER TABLE products_new RENAME TO products")

            # 重建索引
            await conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_products_name ON products (name)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_products_dewu_url ON products (dewu_url)"
            )

            await conn.exec_driver_sql("PRAGMA foreign_keys = ON")
            logger.info("迁移 012: products 表重建完成，废弃列已删除")
        else:
            logger.debug("迁移 012: products 表无需重建（废弃列已不存在）")

        # ── covers 表：加 product_id FK ──────────────────────────────────
        covers_cols_rows = (
            await conn.exec_driver_sql("PRAGMA table_info(covers)")
        ).fetchall()
        covers_col_names = [row[1] for row in covers_cols_rows]

        if "product_id" not in covers_col_names:
            await conn.exec_driver_sql(
                "ALTER TABLE covers ADD COLUMN product_id INTEGER REFERENCES products(id)"
            )
            logger.info("迁移 012: covers.product_id 列已添加")
        else:
            logger.debug("迁移 012: covers.product_id 列已存在，跳过")

    logger.info("迁移 012 完成")
