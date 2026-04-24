"""
Migration 036 - creative current truth explicitization.

Adds explicit current truth fields onto creative_items and backfills them from
the pre-Slice-1 compatibility carriers.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATIVE_ITEM_ADDITIONS = {
    "current_product_name": "ALTER TABLE creative_items ADD COLUMN current_product_name VARCHAR(256)",
    "product_name_mode": "ALTER TABLE creative_items ADD COLUMN product_name_mode VARCHAR(32)",
    "current_cover_asset_type": "ALTER TABLE creative_items ADD COLUMN current_cover_asset_type VARCHAR(32)",
    "current_cover_asset_id": "ALTER TABLE creative_items ADD COLUMN current_cover_asset_id INTEGER REFERENCES covers(id)",
    "cover_mode": "ALTER TABLE creative_items ADD COLUMN cover_mode VARCHAR(32)",
    "current_copywriting_id": "ALTER TABLE creative_items ADD COLUMN current_copywriting_id INTEGER REFERENCES copywritings(id)",
    "current_copywriting_text": "ALTER TABLE creative_items ADD COLUMN current_copywriting_text TEXT",
    "copywriting_mode": "ALTER TABLE creative_items ADD COLUMN copywriting_mode VARCHAR(32)",
}

CREATIVE_ITEM_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_creative_items_current_cover_asset_id ON creative_items(current_cover_asset_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_current_copywriting_id ON creative_items(current_copywriting_id)",
]


async def _backfill_current_truth(conn) -> None:
    creative_rows = (
        await conn.exec_driver_sql(
            """
            SELECT
                id,
                subject_product_id,
                subject_product_name_snapshot,
                main_copywriting_text,
                current_product_name,
                product_name_mode,
                current_cover_asset_type,
                current_cover_asset_id,
                cover_mode,
                current_copywriting_id,
                current_copywriting_text,
                copywriting_mode
            FROM creative_items
            ORDER BY id
            """
        )
    ).fetchall()

    for row in creative_rows:
        (
            creative_id,
            subject_product_id,
            subject_product_name_snapshot,
            main_copywriting_text,
            current_product_name,
            product_name_mode,
            current_cover_asset_type,
            current_cover_asset_id,
            cover_mode,
            current_copywriting_id,
            current_copywriting_text,
            copywriting_mode,
        ) = row

        product_name = None
        if subject_product_id is not None:
            product_name = (
                await conn.exec_driver_sql(
                    "SELECT name FROM products WHERE id = ?",
                    (int(subject_product_id),),
                )
            ).scalar_one_or_none()

        next_current_product_name = current_product_name
        if next_current_product_name is None:
            next_current_product_name = subject_product_name_snapshot or product_name

        next_product_name_mode = product_name_mode
        if next_product_name_mode is None:
            if subject_product_id is not None and (subject_product_name_snapshot is None or subject_product_name_snapshot == product_name):
                next_product_name_mode = "follow_primary_product"
            else:
                next_product_name_mode = "manual"

        next_current_copywriting_text = current_copywriting_text
        if next_current_copywriting_text is None:
            next_current_copywriting_text = main_copywriting_text

        next_copywriting_mode = copywriting_mode
        if next_copywriting_mode is None:
            next_copywriting_mode = "manual"

        next_current_cover_asset_id = current_cover_asset_id
        next_current_cover_asset_type = current_cover_asset_type
        next_cover_mode = cover_mode

        default_product_cover_id = None
        if subject_product_id is not None:
            default_product_cover_id = (
                await conn.exec_driver_sql(
                    """
                    SELECT id
                    FROM covers
                    WHERE product_id = ?
                    ORDER BY id ASC
                    LIMIT 1
                    """,
                    (int(subject_product_id),),
                )
            ).scalar_one_or_none()

        input_cover_id = (
            await conn.exec_driver_sql(
                """
                SELECT material_id
                FROM creative_input_items
                WHERE creative_item_id = ? AND material_type = 'cover'
                ORDER BY sequence ASC, id ASC
                LIMIT 1
                """,
                (int(creative_id),),
            )
        ).scalar_one_or_none()

        if next_current_cover_asset_id is None:
            if default_product_cover_id is not None:
                next_current_cover_asset_id = int(default_product_cover_id)
                next_current_cover_asset_type = "cover"
                next_cover_mode = next_cover_mode or "default_from_primary_product"
            elif input_cover_id is not None:
                next_current_cover_asset_id = int(input_cover_id)
                next_current_cover_asset_type = "cover"
                next_cover_mode = next_cover_mode or "adopted_candidate"

        if next_current_cover_asset_id is not None and next_current_cover_asset_type is None:
            next_current_cover_asset_type = "cover"
        if next_cover_mode is None:
            next_cover_mode = "default_from_primary_product" if subject_product_id is not None else "manual"

        if next_current_product_name is not None and subject_product_name_snapshot != next_current_product_name:
            subject_product_name_snapshot = next_current_product_name
        if next_current_copywriting_text != main_copywriting_text:
            main_copywriting_text = next_current_copywriting_text

        await conn.exec_driver_sql(
            """
            UPDATE creative_items
            SET
                subject_product_name_snapshot = ?,
                main_copywriting_text = ?,
                current_product_name = ?,
                product_name_mode = ?,
                current_cover_asset_type = ?,
                current_cover_asset_id = ?,
                cover_mode = ?,
                current_copywriting_id = ?,
                current_copywriting_text = ?,
                copywriting_mode = ?
            WHERE id = ?
            """,
            (
                subject_product_name_snapshot,
                main_copywriting_text,
                next_current_product_name,
                next_product_name_mode,
                next_current_cover_asset_type,
                next_current_cover_asset_id,
                next_cover_mode,
                current_copywriting_id,
                next_current_copywriting_text,
                next_copywriting_mode,
                int(creative_id),
            ),
        )


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_item_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        if not creative_item_columns:
            logger.info("Migration 036: creative_items table does not exist, skipping")
            return

        existing_columns = {column[1] for column in creative_item_columns}
        for column_name, sql in CREATIVE_ITEM_ADDITIONS.items():
            if column_name in existing_columns:
                continue
            await conn.exec_driver_sql(sql)
            logger.info("Migration 036: added creative_items.{}", column_name)

        for sql in CREATIVE_ITEM_INDEXES:
            await conn.exec_driver_sql(sql)

        await _backfill_current_truth(conn)

    logger.info("Migration 036 complete")
