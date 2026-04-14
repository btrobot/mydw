"""
迁移 023 — 创建 remote_auth_sessions 表

变更：
  - 新建 remote_auth_sessions 表，持久化本地机器授权会话的 non-secret state
  - 新建 auth_state / remote_user_id / license_status / device_id 索引

设计原则：幂等 — 表已存在则跳过。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        tables = (
            await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='remote_auth_sessions'"
            )
        ).fetchall()

        if not tables:
            await conn.exec_driver_sql("""
                CREATE TABLE remote_auth_sessions (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    auth_state              VARCHAR(32) NOT NULL DEFAULT 'unauthenticated',
                    remote_user_id          VARCHAR(128),
                    display_name            VARCHAR(256),
                    license_status          VARCHAR(32),
                    entitlements_snapshot   TEXT,
                    expires_at              DATETIME,
                    last_verified_at        DATETIME,
                    offline_grace_until     DATETIME,
                    denial_reason           VARCHAR(64),
                    device_id               VARCHAR(128),
                    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_remote_auth_sessions_auth_state ON remote_auth_sessions (auth_state)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_remote_auth_sessions_remote_user_id ON remote_auth_sessions (remote_user_id)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_remote_auth_sessions_license_status ON remote_auth_sessions (license_status)"
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_remote_auth_sessions_device_id ON remote_auth_sessions (device_id)"
            )
            logger.info("迁移 023: remote_auth_sessions 表已创建")
        else:
            logger.debug("迁移 023: remote_auth_sessions 表已存在，跳过")

    logger.info("迁移 023 完成")
