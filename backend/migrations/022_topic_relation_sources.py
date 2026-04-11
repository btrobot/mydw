"""
迁移 022 — 话题关系 canonical source 表

变更：
  - 新建 global_topics 关联表
  - 新建 publish_profile_topics 关联表
  - 新建 topic_group_topics 关联表
  - 从 legacy JSON 列回填数据：
    - publish_config.global_topic_ids -> global_topics
    - publish_profiles.global_topic_ids -> publish_profile_topics
    - topic_groups.topic_ids -> topic_group_topics

设计原则：
  - 幂等：表已存在则跳过创建
  - 回填使用 INSERT OR IGNORE，重复运行不重复插入
"""
from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS global_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL REFERENCES topics(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(topic_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_global_topics_topic_id ON global_topics(topic_id)",
    """
    CREATE TABLE IF NOT EXISTS publish_profile_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL REFERENCES publish_profiles(id) ON DELETE CASCADE,
        topic_id INTEGER NOT NULL REFERENCES topics(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(profile_id, topic_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_publish_profile_topics_profile_id ON publish_profile_topics(profile_id)",
    "CREATE INDEX IF NOT EXISTS ix_publish_profile_topics_topic_id ON publish_profile_topics(topic_id)",
    """
    CREATE TABLE IF NOT EXISTS topic_group_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL REFERENCES topic_groups(id) ON DELETE CASCADE,
        topic_id INTEGER NOT NULL REFERENCES topics(id),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE(group_id, topic_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_topic_group_topics_group_id ON topic_group_topics(group_id)",
    "CREATE INDEX IF NOT EXISTS ix_topic_group_topics_topic_id ON topic_group_topics(topic_id)",
]


def _parse_topic_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(parsed, list):
        return []

    ordered: list[int] = []
    seen: set[int] = set()
    for value in parsed:
        if isinstance(value, int) and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等。"""
    async with engine.begin() as conn:
        for sql in CREATE_STATEMENTS:
            await conn.exec_driver_sql(sql)
        logger.info("迁移 022: 话题关系 canonical source 表创建完成")

        publish_config_rows = (
            await conn.exec_driver_sql(
                "SELECT global_topic_ids FROM publish_config ORDER BY id LIMIT 1"
            )
        ).fetchall()
        for (raw_topic_ids,) in publish_config_rows:
            for order, topic_id in enumerate(_parse_topic_ids(raw_topic_ids)):
                await conn.exec_driver_sql(
                    "INSERT OR IGNORE INTO global_topics (topic_id, sort_order) VALUES (?, ?)",
                    (topic_id, order),
                )

        publish_profile_rows = (
            await conn.exec_driver_sql(
                "SELECT id, global_topic_ids FROM publish_profiles"
            )
        ).fetchall()
        for profile_id, raw_topic_ids in publish_profile_rows:
            for order, topic_id in enumerate(_parse_topic_ids(raw_topic_ids)):
                await conn.exec_driver_sql(
                    "INSERT OR IGNORE INTO publish_profile_topics (profile_id, topic_id, sort_order) VALUES (?, ?, ?)",
                    (profile_id, topic_id, order),
                )

        topic_group_rows = (
            await conn.exec_driver_sql(
                "SELECT id, topic_ids FROM topic_groups"
            )
        ).fetchall()
        for group_id, raw_topic_ids in topic_group_rows:
            for order, topic_id in enumerate(_parse_topic_ids(raw_topic_ids)):
                await conn.exec_driver_sql(
                    "INSERT OR IGNORE INTO topic_group_topics (group_id, topic_id, sort_order) VALUES (?, ?, ?)",
                    (group_id, topic_id, order),
                )

        logger.info("迁移 022: 旧 JSON 话题数据回填完成")

    logger.info("迁移 022 完成")
