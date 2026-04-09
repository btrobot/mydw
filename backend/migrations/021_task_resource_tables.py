"""
迁移 021 — 任务资源关联表（资源集合模型）

变更：
  - 新建 task_videos 关联表 (task_id, video_id, sort_order)
  - 新建 task_copywritings 关联表 (task_id, copywriting_id, sort_order)
  - 新建 task_covers 关联表 (task_id, cover_id, sort_order)
  - 新建 task_audios 关联表 (task_id, audio_id, sort_order)
  - 迁移旧 FK 数据到关联表
  - 迁移 source_video_ids JSON 数据到 task_videos

设计原则：幂等 — 表已存在则跳过创建，数据已迁移则跳过插入。
"""
from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS task_videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        video_id INTEGER NOT NULL REFERENCES videos(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(task_id, video_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_task_videos_task_id ON task_videos(task_id)",
    "CREATE INDEX IF NOT EXISTS ix_task_videos_video_id ON task_videos(video_id)",
    """
    CREATE TABLE IF NOT EXISTS task_copywritings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        copywriting_id INTEGER NOT NULL REFERENCES copywritings(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(task_id, copywriting_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_task_copywritings_task_id ON task_copywritings(task_id)",
    "CREATE INDEX IF NOT EXISTS ix_task_copywritings_copywriting_id ON task_copywritings(copywriting_id)",
    """
    CREATE TABLE IF NOT EXISTS task_covers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        cover_id INTEGER NOT NULL REFERENCES covers(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(task_id, cover_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_task_covers_task_id ON task_covers(task_id)",
    "CREATE INDEX IF NOT EXISTS ix_task_covers_cover_id ON task_covers(cover_id)",
    """
    CREATE TABLE IF NOT EXISTS task_audios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        audio_id INTEGER NOT NULL REFERENCES audios(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(task_id, audio_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_task_audios_task_id ON task_audios(task_id)",
    "CREATE INDEX IF NOT EXISTS ix_task_audios_audio_id ON task_audios(audio_id)",
]


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # 1. 创建关联表
        for sql in CREATE_STATEMENTS:
            await conn.exec_driver_sql(sql)
        logger.info("迁移 021: 关联表创建完成")

        # 2. 迁移旧 FK 数据 — video_id
        await conn.exec_driver_sql(
            """
            INSERT OR IGNORE INTO task_videos (task_id, video_id, sort_order)
            SELECT id, video_id, 0 FROM tasks WHERE video_id IS NOT NULL
            """
        )

        # 3. 迁移 source_video_ids JSON 数据
        rows = (
            await conn.exec_driver_sql(
                "SELECT id, source_video_ids FROM tasks WHERE source_video_ids IS NOT NULL AND source_video_ids != ''"
            )
        ).fetchall()
        for task_id, raw in rows:
            try:
                vid_ids = json.loads(raw)
                if not isinstance(vid_ids, list):
                    continue
                for order, vid_id in enumerate(vid_ids):
                    if isinstance(vid_id, int):
                        await conn.exec_driver_sql(
                            "INSERT OR IGNORE INTO task_videos (task_id, video_id, sort_order) VALUES (?, ?, ?)",
                            (task_id, vid_id, order),
                        )
            except (ValueError, TypeError):
                logger.warning("迁移 021: 解析 source_video_ids 失败, task_id={}", task_id)

        # 4. 迁移旧 FK 数据 — copywriting_id, cover_id, audio_id
        await conn.exec_driver_sql(
            """
            INSERT OR IGNORE INTO task_copywritings (task_id, copywriting_id, sort_order)
            SELECT id, copywriting_id, 0 FROM tasks WHERE copywriting_id IS NOT NULL
            """
        )
        await conn.exec_driver_sql(
            """
            INSERT OR IGNORE INTO task_covers (task_id, cover_id, sort_order)
            SELECT id, cover_id, 0 FROM tasks WHERE cover_id IS NOT NULL
            """
        )
        await conn.exec_driver_sql(
            """
            INSERT OR IGNORE INTO task_audios (task_id, audio_id, sort_order)
            SELECT id, audio_id, 0 FROM tasks WHERE audio_id IS NOT NULL
            """
        )

        logger.info("迁移 021: 旧 FK 数据迁移完成")

    logger.info("迁移 021 完成")
