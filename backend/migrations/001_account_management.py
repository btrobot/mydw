"""
迁移 001 — 账号管理字段扩展

新增字段：
  - phone_encrypted   TEXT
  - dewu_nickname     VARCHAR(128)
  - dewu_uid          VARCHAR(64)
  - avatar_url        VARCHAR(512)
  - tags              TEXT  DEFAULT '[]'
  - remark            TEXT
  - session_expires_at DATETIME
  - last_health_check  DATETIME
  - login_fail_count   INTEGER  DEFAULT 0

设计原则：幂等 — 重复执行不报错。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


# (列名, DDL 片段)
_COLUMNS: list[tuple[str, str]] = [
    ("phone_encrypted",    "TEXT"),
    ("dewu_nickname",      "VARCHAR(128)"),
    ("dewu_uid",           "VARCHAR(64)"),
    ("avatar_url",         "VARCHAR(512)"),
    ("tags",               "TEXT DEFAULT '[]'"),
    ("remark",             "TEXT"),
    ("session_expires_at", "DATETIME"),
    ("last_health_check",  "DATETIME"),
    ("login_fail_count",   "INTEGER DEFAULT 0"),
]


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等（已存在的列跳过）。"""
    async with engine.begin() as conn:
        # 获取 accounts 表现有列名
        result = await conn.exec_driver_sql("PRAGMA table_info(accounts)")
        rows = result.fetchall()
        existing_columns: set[str] = {row[1] for row in rows}

        for col_name, col_def in _COLUMNS:
            if col_name in existing_columns:
                logger.debug("迁移 001: 列 {} 已存在，跳过", col_name)
                continue
            ddl = f"ALTER TABLE accounts ADD COLUMN {col_name} {col_def}"
            await conn.exec_driver_sql(ddl)
            logger.info("迁移 001: 新增列 {}", col_name)

    logger.info("迁移 001 执行完成")
