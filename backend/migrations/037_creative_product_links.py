"""
Migration 037 - creative product links.

Adds creative_product_links as the canonical primary-product authority surface
and backfills it from the legacy subject_product_id mirror.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_CREATIVE_PRODUCT_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS creative_product_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    sort_order INTEGER NOT NULL DEFAULT 1,
    is_primary BOOLEAN NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    source_mode VARCHAR(32) NOT NULL DEFAULT 'manual_add',
    created_at DATETIME,
    updated_at DATETIME,
    CONSTRAINT uq_creative_product_links_creative_product UNIQUE (creative_item_id, product_id)
)
"""

CREATIVE_PRODUCT_LINKS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_product_links_creative_item_id ON creative_product_links(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_product_links_product_id ON creative_product_links(product_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_creative_product_links_primary_per_creative ON creative_product_links(creative_item_id) WHERE is_primary = 1",
]


async def _backfill_product_links(conn) -> None:
    creative_item_columns = {
        row[1]
        for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
    }
    if "subject_product_id" not in creative_item_columns:
        logger.info("Migration 037: creative_items.subject_product_id missing, skip backfill")
        return

    creative_rows = (
        await conn.exec_driver_sql(
            """
            SELECT id, subject_product_id
            FROM creative_items
            ORDER BY id
            """
        )
    ).fetchall()

    for creative_id, subject_product_id in creative_rows:
        if subject_product_id is None:
            continue

        existing_links = (
            await conn.exec_driver_sql(
                """
                SELECT id, product_id
                FROM creative_product_links
                WHERE creative_item_id = ?
                ORDER BY sort_order ASC, id ASC
                """,
                (int(creative_id),),
            )
        ).fetchall()

        if not existing_links:
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_product_links (
                    creative_item_id, product_id, sort_order, is_primary, enabled, source_mode
                ) VALUES (?, ?, 1, 1, 1, 'import_bootstrap')
                """,
                (int(creative_id), int(subject_product_id)),
            )
            continue

        product_ids = [int(row[1]) for row in existing_links]
        if int(subject_product_id) not in product_ids:
            await conn.exec_driver_sql(
                """
                INSERT INTO creative_product_links (
                    creative_item_id, product_id, sort_order, is_primary, enabled, source_mode
                ) VALUES (?, ?, ?, 1, 1, 'import_bootstrap')
                """,
                (int(creative_id), int(subject_product_id), len(existing_links) + 1),
            )

        await conn.exec_driver_sql(
            """
            UPDATE creative_product_links
            SET is_primary = CASE WHEN product_id = ? THEN 1 ELSE 0 END
            WHERE creative_item_id = ?
            """,
            (int(subject_product_id), int(creative_id)),
        )


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_items = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='creative_items'"
            )
        ).fetchone()
        if creative_items is None:
            logger.info("Migration 037: creative_items table does not exist, skipping")
            return

        await conn.exec_driver_sql(CREATE_CREATIVE_PRODUCT_LINKS_TABLE)
        for sql in CREATIVE_PRODUCT_LINKS_INDEXES:
            await conn.exec_driver_sql(sql)

        await _backfill_product_links(conn)

    logger.info("Migration 037 complete")
