"""
Migration 035 - creative phase 4 snapshot retirement.

Backfills any remaining legacy creative snapshot carriers into canonical
creative_input_items, then removes the retired snapshot storage/table layer.
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


LEGACY_CREATIVE_ITEM_COLUMNS = (
    "input_video_ids",
    "input_copywriting_ids",
    "input_cover_ids",
    "input_audio_ids",
    "input_topic_ids",
    "input_snapshot_hash",
)

SNAPSHOT_FIELD_ORDER: tuple[tuple[str, str], ...] = (
    ("video_ids", "video"),
    ("copywriting_ids", "copywriting"),
    ("cover_ids", "cover"),
    ("audio_ids", "audio"),
    ("topic_ids", "topic"),
)

CREATIVE_ITEM_SOURCE_COLUMNS: dict[str, str] = {
    "video_ids": "input_video_ids",
    "copywriting_ids": "input_copywriting_ids",
    "cover_ids": "input_cover_ids",
    "audio_ids": "input_audio_ids",
    "topic_ids": "input_topic_ids",
}

REBUILD_CREATIVE_ITEMS_SQL = """
CREATE TABLE creative_items__phase4_cleanup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creative_no VARCHAR(64) NOT NULL,
    title VARCHAR(256),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_INPUT',
    current_version_id INTEGER REFERENCES creative_versions(id),
    latest_version_no INTEGER NOT NULL DEFAULT 0,
    generation_error_msg TEXT,
    generation_failed_at DATETIME,
    subject_product_id INTEGER REFERENCES products(id),
    subject_product_name_snapshot VARCHAR(256),
    main_copywriting_text TEXT,
    target_duration_seconds INTEGER,
    input_profile_id INTEGER REFERENCES publish_profiles(id),
    created_at DATETIME,
    updated_at DATETIME
)
"""

COPY_CREATIVE_ITEMS_SQL = """
INSERT INTO creative_items__phase4_cleanup (
    id,
    creative_no,
    title,
    status,
    current_version_id,
    latest_version_no,
    generation_error_msg,
    generation_failed_at,
    subject_product_id,
    subject_product_name_snapshot,
    main_copywriting_text,
    target_duration_seconds,
    input_profile_id,
    created_at,
    updated_at
)
SELECT
    id,
    creative_no,
    title,
    status,
    current_version_id,
    latest_version_no,
    generation_error_msg,
    generation_failed_at,
    subject_product_id,
    subject_product_name_snapshot,
    main_copywriting_text,
    target_duration_seconds,
    input_profile_id,
    created_at,
    updated_at
FROM creative_items
"""

RECREATE_CREATIVE_ITEM_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_creative_items_creative_no ON creative_items(creative_no)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_status ON creative_items(status)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_current_version_id ON creative_items(current_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_subject_product_id ON creative_items(subject_product_id)",
    "CREATE INDEX IF NOT EXISTS ix_creative_items_input_profile_id ON creative_items(input_profile_id)",
]

SNAPSHOT_DROP_STATEMENTS = [
    "DROP INDEX IF EXISTS ix_creative_input_snapshots_snapshot_hash",
    "DROP INDEX IF EXISTS ix_creative_input_snapshots_profile_id",
    "DROP INDEX IF EXISTS ix_creative_input_snapshots_creative_item_id",
    "DROP TABLE IF EXISTS creative_input_snapshots",
]


def _decode_id_list(raw_value: Any) -> list[int]:
    if raw_value in (None, ""):
        return []
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    values: list[int] = []
    for item in parsed:
        try:
            values.append(int(item))
        except (TypeError, ValueError):
            continue
    return values


async def _backfill_missing_input_items(conn) -> None:
    creative_item_columns = {
        row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
    }
    if "input_profile_id" not in creative_item_columns:
        return

    snapshot_table_exists = bool(
        (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='creative_input_snapshots'"
            )
        ).fetchone()
    )
    available_legacy_sources = {
        field_name: column_name
        for field_name, column_name in CREATIVE_ITEM_SOURCE_COLUMNS.items()
        if column_name in creative_item_columns
    }
    if not snapshot_table_exists and not available_legacy_sources:
        return

    item_counts = {
        row[0]: row[1]
        for row in (
            await conn.exec_driver_sql(
                "SELECT creative_item_id, COUNT(*) FROM creative_input_items GROUP BY creative_item_id"
            )
        ).fetchall()
    }

    select_columns = ["id", "input_profile_id", *available_legacy_sources.values()]
    creative_rows = (
        await conn.exec_driver_sql(
            f"""
            SELECT
                {", ".join(select_columns)}
            FROM creative_items
            ORDER BY id
            """
        )
    ).fetchall()

    snapshot_rows: dict[int, dict[str, Any]] = {}
    if snapshot_table_exists:
        for row in (
            await conn.exec_driver_sql(
                """
                SELECT
                    creative_item_id,
                    profile_id,
                    video_ids,
                    copywriting_ids,
                    cover_ids,
                    audio_ids,
                    topic_ids
                FROM creative_input_snapshots
                """
            )
        ).fetchall():
            snapshot_rows[int(row[0])] = {
                "profile_id": row[1],
                "video_ids": _decode_id_list(row[2]),
                "copywriting_ids": _decode_id_list(row[3]),
                "cover_ids": _decode_id_list(row[4]),
                "audio_ids": _decode_id_list(row[5]),
                "topic_ids": _decode_id_list(row[6]),
            }

    for row in creative_rows:
        creative_row = dict(zip(select_columns, row))
        creative_id = int(creative_row["id"])
        if item_counts.get(creative_id, 0) > 0:
            continue

        snapshot_row = snapshot_rows.get(creative_id)
        effective_profile_id = creative_row["input_profile_id"]
        if effective_profile_id is None and snapshot_row is not None and snapshot_row["profile_id"] is not None:
            effective_profile_id = int(snapshot_row["profile_id"])
            await conn.exec_driver_sql(
                "UPDATE creative_items SET input_profile_id = ? WHERE id = ?",
                (effective_profile_id, creative_id),
            )

        source_lists = {
            field_name: _decode_id_list(creative_row.get(column_name))
            for field_name, column_name in available_legacy_sources.items()
        }
        for field_name in CREATIVE_ITEM_SOURCE_COLUMNS:
            source_lists.setdefault(field_name, [])
        if snapshot_row is not None:
            for field_name in source_lists:
                if not source_lists[field_name]:
                    source_lists[field_name] = list(snapshot_row[field_name])

        sequence = 1
        material_instance_counts: defaultdict[tuple[str, int], int] = defaultdict(int)
        for field_name, material_type in SNAPSHOT_FIELD_ORDER:
            for material_id in source_lists[field_name]:
                material_key = (material_type, int(material_id))
                material_instance_counts[material_key] += 1
                await conn.exec_driver_sql(
                    """
                    INSERT INTO creative_input_items (
                        creative_item_id,
                        material_type,
                        material_id,
                        sequence,
                        instance_no,
                        enabled
                    ) VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (
                        creative_id,
                        material_type,
                        int(material_id),
                        sequence,
                        material_instance_counts[material_key],
                    ),
                )
                sequence += 1


async def _rebuild_creative_items_without_legacy_columns(conn) -> None:
    creative_item_columns = {
        row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
    }
    if not any(column_name in creative_item_columns for column_name in LEGACY_CREATIVE_ITEM_COLUMNS):
        return

    await conn.exec_driver_sql("DROP INDEX IF EXISTS ix_creative_items_input_snapshot_hash")
    await conn.exec_driver_sql("DROP TABLE IF EXISTS creative_items__phase4_cleanup")
    await conn.exec_driver_sql(REBUILD_CREATIVE_ITEMS_SQL)
    await conn.exec_driver_sql(COPY_CREATIVE_ITEMS_SQL)
    await conn.exec_driver_sql("DROP TABLE creative_items")
    await conn.exec_driver_sql("ALTER TABLE creative_items__phase4_cleanup RENAME TO creative_items")
    for sql in RECREATE_CREATIVE_ITEM_INDEXES:
        await conn.exec_driver_sql(sql)
    logger.info("Migration 035: rebuilt creative_items without legacy snapshot columns")


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        creative_item_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_items)")).fetchall()
        if not creative_item_columns:
            logger.info("Migration 035: creative_items table missing, skipping")
            return

        await _backfill_missing_input_items(conn)

        for sql in SNAPSHOT_DROP_STATEMENTS:
            await conn.exec_driver_sql(sql)

        await _rebuild_creative_items_without_legacy_columns(conn)

    logger.info("Migration 035 complete")
