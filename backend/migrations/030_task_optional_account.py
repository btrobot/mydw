"""
Migration 030 - allow tasks without a pre-bound account.

SQLite cannot drop NOT NULL in-place, so rebuild the tasks table with
`account_id` nullable while preserving existing data and indexes.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


TASK_COLUMNS = [
    "id",
    "account_id",
    "product_id",
    "video_id",
    "copywriting_id",
    "audio_id",
    "cover_id",
    "status",
    "publish_time",
    "error_msg",
    "priority",
    "name",
    "description",
    "source_video_ids",
    "composition_template",
    "composition_params",
    "composition_job_id",
    "final_video_path",
    "final_video_duration",
    "final_video_size",
    "scheduled_time",
    "retry_count",
    "dewu_video_id",
    "dewu_video_url",
    "profile_id",
    "batch_id",
    "failed_at_status",
    "created_at",
    "updated_at",
    "creative_item_id",
    "creative_version_id",
    "task_kind",
]


CREATE_TASKS_SQL = """
CREATE TABLE tasks_new (
    id INTEGER NOT NULL PRIMARY KEY,
    account_id INTEGER,
    product_id INTEGER,
    video_id INTEGER,
    copywriting_id INTEGER,
    audio_id INTEGER,
    cover_id INTEGER,
    status VARCHAR(32),
    publish_time DATETIME,
    error_msg TEXT,
    priority INTEGER,
    name VARCHAR(256),
    description VARCHAR,
    source_video_ids VARCHAR,
    composition_template VARCHAR(64),
    composition_params VARCHAR,
    composition_job_id INTEGER,
    final_video_path VARCHAR(512),
    final_video_duration INTEGER,
    final_video_size INTEGER,
    scheduled_time DATETIME,
    retry_count INTEGER,
    dewu_video_id VARCHAR(128),
    dewu_video_url VARCHAR(512),
    profile_id INTEGER,
    batch_id VARCHAR(64),
    failed_at_status VARCHAR(32),
    created_at DATETIME,
    updated_at DATETIME,
    creative_item_id INTEGER REFERENCES creative_items(id),
    creative_version_id INTEGER REFERENCES creative_versions(id),
    task_kind VARCHAR(32),
    FOREIGN KEY(account_id) REFERENCES accounts (id),
    FOREIGN KEY(product_id) REFERENCES products (id),
    FOREIGN KEY(video_id) REFERENCES videos (id),
    FOREIGN KEY(copywriting_id) REFERENCES copywritings (id),
    FOREIGN KEY(audio_id) REFERENCES audios (id),
    FOREIGN KEY(cover_id) REFERENCES covers (id),
    FOREIGN KEY(profile_id) REFERENCES publish_profiles (id)
)
"""


TASK_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_tasks_account_id ON tasks(account_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_audio_id ON tasks(audio_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_batch_id ON tasks(batch_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_composition_job_id ON tasks(composition_job_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_copywriting_id ON tasks(copywriting_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_cover_id ON tasks(cover_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_creative_item_id ON tasks(creative_item_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_creative_version_id ON tasks(creative_version_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_profile_id ON tasks(profile_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_publish_time ON tasks(publish_time)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_scheduled_time ON tasks(scheduled_time)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_task_kind ON tasks(task_kind)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_video_id ON tasks(video_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_composition_job_id ON tasks(composition_job_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_time ON tasks(scheduled_time)",
]


async def run_migration(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        task_columns = (await conn.exec_driver_sql("PRAGMA table_info(tasks)")).fetchall()
        if not task_columns:
            logger.info("Migration 030: tasks table does not exist, skipping")
            return

        account_column = next((column for column in task_columns if column[1] == "account_id"), None)
        if account_column is None:
            logger.info("Migration 030: tasks.account_id does not exist, skipping")
            return

        notnull_flag = account_column[3]
        if notnull_flag == 0:
            logger.info("Migration 030: tasks.account_id already nullable")
            return

        logger.info("Migration 030: rebuilding tasks table to make account_id nullable")
        columns_csv = ", ".join(TASK_COLUMNS)

        await conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
        await conn.exec_driver_sql("DROP TABLE IF EXISTS tasks_new")
        await conn.exec_driver_sql(CREATE_TASKS_SQL)
        await conn.exec_driver_sql(
            f"INSERT INTO tasks_new ({columns_csv}) SELECT {columns_csv} FROM tasks"
        )
        await conn.exec_driver_sql("DROP TABLE tasks")
        await conn.exec_driver_sql("ALTER TABLE tasks_new RENAME TO tasks")

        for sql in TASK_INDEXES:
            await conn.exec_driver_sql(sql)

        await conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    logger.info("Migration 030 complete")
