"""
迁移 025 — Creative Phase B review invariant 基础
变更：
  - 为 creative_versions 增加 parent_version_id
  - 新建 check_records 表
设计原则：幂等；字段/表已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS check_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creative_item_id INTEGER NOT NULL REFERENCES creative_items(id),
        creative_version_id INTEGER NOT NULL REFERENCES creative_versions(id),
        conclusion VARCHAR(32) NOT NULL CHECK (conclusion IN ('APPROVED', 'REWORK_REQUIRED', 'REJECTED')),
        rework_type VARCHAR(64),
        note TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CHECK (conclusion != 'REWORK_REQUIRED' OR rework_type IS NOT NULL)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_check_records_creative_item_id ON check_records(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_check_records_creative_version_id ON check_records(creative_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_check_records_conclusion ON check_records(conclusion)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        version_columns = (
            await conn.exec_driver_sql("PRAGMA table_info(creative_versions)")
        ).fetchall()
        existing_version_columns = {col[1] for col in version_columns}

        if "parent_version_id" not in existing_version_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE creative_versions ADD COLUMN parent_version_id INTEGER REFERENCES creative_versions(id)"
            )
            logger.info("迁移 025: 添加字段 creative_versions.parent_version_id")

        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_creative_versions_parent_version_id ON creative_versions(parent_version_id)"
        )

        for sql in CREATE_TABLE_STATEMENTS:
            await conn.exec_driver_sql(sql)

    logger.info("迁移 025 完成")
