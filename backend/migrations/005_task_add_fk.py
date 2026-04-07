"""
迁移 005 — Task 增加素材 FK + TaskTopic 关联表 (SP3-01, SP3-02)

变更：
  tasks 表新增列：
    - video_id       INTEGER REFERENCES videos(id)
    - copywriting_id INTEGER REFERENCES copywritings(id)
    - audio_id       INTEGER REFERENCES audios(id)

  新建表：
    - task_topics (id, task_id, topic_id)

设计原则：幂等 — PRAGMA table_info 检查列是否已存在，sqlite_master 检查表是否已存在。
旧字段 video_path / content / topic / cover_path / audio_path 保留不动（双写期）。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        # ── 检查 tasks 表现有列 ──────────────────────────────────────────
        col_info = (
            await conn.exec_driver_sql("PRAGMA table_info(tasks)")
        ).fetchall()
        existing_cols: set[str] = {row[1] for row in col_info}

        # video_id
        if "video_id" not in existing_cols:
            await conn.exec_driver_sql(
                "ALTER TABLE tasks ADD COLUMN video_id INTEGER REFERENCES videos(id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_tasks_video_id ON tasks (video_id)"
            )
            logger.info("迁移 005: tasks.video_id 列已添加")
        else:
            logger.debug("迁移 005: tasks.video_id 已存在，跳过")

        # copywriting_id
        if "copywriting_id" not in existing_cols:
            await conn.exec_driver_sql(
                "ALTER TABLE tasks ADD COLUMN copywriting_id INTEGER REFERENCES copywritings(id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_tasks_copywriting_id ON tasks (copywriting_id)"
            )
            logger.info("迁移 005: tasks.copywriting_id 列已添加")
        else:
            logger.debug("迁移 005: tasks.copywriting_id 已存在，跳过")

        # audio_id
        if "audio_id" not in existing_cols:
            await conn.exec_driver_sql(
                "ALTER TABLE tasks ADD COLUMN audio_id INTEGER REFERENCES audios(id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_tasks_audio_id ON tasks (audio_id)"
            )
            logger.info("迁移 005: tasks.audio_id 列已添加")
        else:
            logger.debug("迁移 005: tasks.audio_id 已存在，跳过")

        # ── task_topics 表 ───────────────────────────────────────────────
        table_exists = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='task_topics'"
            )
        ).fetchone()

        if not table_exists:
            await conn.exec_driver_sql(
                """
                CREATE TABLE task_topics (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id  INTEGER NOT NULL REFERENCES tasks(id),
                    topic_id INTEGER NOT NULL REFERENCES topics(id)
                )
                """
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_task_topics_task_id ON task_topics (task_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_task_topics_topic_id ON task_topics (topic_id)"
            )
            logger.info("迁移 005: task_topics 表已创建")
        else:
            logger.debug("迁移 005: task_topics 表已存在，跳过")

    logger.info("迁移 005 完成")
