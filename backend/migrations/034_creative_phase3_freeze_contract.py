"""
Migration 034 - Creative Phase 3 freeze contract landing.

Adds explicit version adopted-value fields plus publish-package freeze fields so
Phase 3 can expose frozen truth without relying on task collections as the
primary contract surface.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATIVE_VERSION_ADDITIONS = {
    "actual_duration_seconds": "ALTER TABLE creative_versions ADD COLUMN actual_duration_seconds INTEGER",
    "final_video_path": "ALTER TABLE creative_versions ADD COLUMN final_video_path VARCHAR(512)",
    "final_product_name": "ALTER TABLE creative_versions ADD COLUMN final_product_name VARCHAR(256)",
    "final_copywriting_text": "ALTER TABLE creative_versions ADD COLUMN final_copywriting_text TEXT",
}

PACKAGE_RECORD_ADDITIONS = {
    "publish_profile_id": "ALTER TABLE package_records ADD COLUMN publish_profile_id INTEGER REFERENCES publish_profiles(id)",
    "frozen_video_path": "ALTER TABLE package_records ADD COLUMN frozen_video_path VARCHAR(512)",
    "frozen_cover_path": "ALTER TABLE package_records ADD COLUMN frozen_cover_path VARCHAR(512)",
    "frozen_duration_seconds": "ALTER TABLE package_records ADD COLUMN frozen_duration_seconds INTEGER",
    "frozen_product_name": "ALTER TABLE package_records ADD COLUMN frozen_product_name VARCHAR(256)",
    "frozen_copywriting_text": "ALTER TABLE package_records ADD COLUMN frozen_copywriting_text TEXT",
}

PACKAGE_RECORD_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_package_records_publish_profile_id ON package_records(publish_profile_id)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        version_columns = (await conn.exec_driver_sql("PRAGMA table_info(creative_versions)")).fetchall()
        package_columns = (await conn.exec_driver_sql("PRAGMA table_info(package_records)")).fetchall()
        if not version_columns or not package_columns:
            logger.info("Migration 034: creative_versions or package_records table missing, skipping")
            return

        existing_version_columns = {column[1] for column in version_columns}
        existing_package_columns = {column[1] for column in package_columns}

        for column_name, sql in CREATIVE_VERSION_ADDITIONS.items():
            if column_name in existing_version_columns:
                continue
            await conn.exec_driver_sql(sql)
            logger.info("Migration 034: added creative_versions.{}", column_name)

        for column_name, sql in PACKAGE_RECORD_ADDITIONS.items():
            if column_name in existing_package_columns:
                continue
            await conn.exec_driver_sql(sql)
            logger.info("Migration 034: added package_records.{}", column_name)

        for sql in PACKAGE_RECORD_INDEXES:
            await conn.exec_driver_sql(sql)

    logger.info("Migration 034 complete")
