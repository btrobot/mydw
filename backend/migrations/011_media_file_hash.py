"""
迁移 011 — covers/audios 表加 file_hash 列，videos/covers/audios 加 file_hash 索引

变更：
  - covers 表加 file_hash VARCHAR(64)（如不存在）
  - audios 表加 file_hash VARCHAR(64)（如不存在）
  - 创建索引 ix_videos_file_hash（如不存在）
  - 创建索引 ix_covers_file_hash（如不存在）
  - 创建索引 ix_audios_file_hash（如不存在）

设计原则：幂等 — 列/索引已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:

        # --- covers.file_hash 列 ---
        covers_cols = (
            await conn.exec_driver_sql("PRAGMA table_info(covers)")
        ).fetchall()
        covers_col_names = [row[1] for row in covers_cols]
        if "file_hash" not in covers_col_names:
            await conn.exec_driver_sql(
                "ALTER TABLE covers ADD COLUMN file_hash VARCHAR(64)"
            )
            logger.info("迁移 011: covers.file_hash 列已添加")
        else:
            logger.debug("迁移 011: covers.file_hash 列已存在，跳过")

        # --- audios.file_hash 列 ---
        audios_cols = (
            await conn.exec_driver_sql("PRAGMA table_info(audios)")
        ).fetchall()
        audios_col_names = [row[1] for row in audios_cols]
        if "file_hash" not in audios_col_names:
            await conn.exec_driver_sql(
                "ALTER TABLE audios ADD COLUMN file_hash VARCHAR(64)"
            )
            logger.info("迁移 011: audios.file_hash 列已添加")
        else:
            logger.debug("迁移 011: audios.file_hash 列已存在，跳过")

        # --- ix_videos_file_hash 索引 ---
        idx_videos = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_videos_file_hash'"
            )
        ).fetchall()
        if not idx_videos:
            await conn.exec_driver_sql(
                "CREATE INDEX ix_videos_file_hash ON videos (file_hash)"
            )
            logger.info("迁移 011: ix_videos_file_hash 索引已创建")
        else:
            logger.debug("迁移 011: ix_videos_file_hash 已存在，跳过")

        # --- ix_covers_file_hash 索引 ---
        idx_covers = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_covers_file_hash'"
            )
        ).fetchall()
        if not idx_covers:
            await conn.exec_driver_sql(
                "CREATE INDEX ix_covers_file_hash ON covers (file_hash)"
            )
            logger.info("迁移 011: ix_covers_file_hash 索引已创建")
        else:
            logger.debug("迁移 011: ix_covers_file_hash 已存在，跳过")

        # --- ix_audios_file_hash 索引 ---
        idx_audios = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_audios_file_hash'"
            )
        ).fetchall()
        if not idx_audios:
            await conn.exec_driver_sql(
                "CREATE INDEX ix_audios_file_hash ON audios (file_hash)"
            )
            logger.info("迁移 011: ix_audios_file_hash 索引已创建")
        else:
            logger.debug("迁移 011: ix_audios_file_hash 已存在，跳过")

    logger.info("迁移 011 完成")
