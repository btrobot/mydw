"""
迁移 004 — Material 表数据分流 (SP1-07)

将 materials 表中的记录按 type 字段迁移到对应的专用表：
  - type="video"  → videos
  - type="text"   → copywritings
  - type="cover"  → covers
  - type="audio"  → audios
  - type="topic"  → topics

设计原则：幂等 — 以 file_path 或 content 去重，已存在则跳过。
不删除、不修改 materials 表（保留兼容层）。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migration(engine: AsyncEngine) -> None:
    """执行迁移，幂等（目标表已有相同记录则跳过）。"""
    async with engine.begin() as conn:
        rows = (await conn.exec_driver_sql("SELECT * FROM materials")).fetchall()

    if not rows:
        logger.info("迁移 004: materials 表为空，无需迁移")
        return

    # 列名映射（SQLite PRAGMA table_info 返回 (cid, name, ...)）
    async with engine.begin() as conn:
        col_info = (await conn.exec_driver_sql("PRAGMA table_info(materials)")).fetchall()
    col_names: list[str] = [c[1] for c in col_info]

    def to_dict(row: Any) -> dict[str, Any]:
        return dict(zip(col_names, row))

    materials = [to_dict(r) for r in rows]

    counts: dict[str, int] = {
        "videos": 0,
        "copywritings": 0,
        "covers": 0,
        "audios": 0,
        "topics": 0,
    }

    logger.info("迁移 004: 开始分流 {} 条 materials 记录", len(materials))

    async with engine.begin() as conn:
        # 预加载各目标表已有的去重键，避免逐行查询
        existing_videos: set[str] = {
            r[0] for r in (await conn.exec_driver_sql(
                "SELECT file_path FROM videos WHERE file_path IS NOT NULL"
            )).fetchall()
        }
        existing_copywritings: set[str] = {
            r[0] for r in (await conn.exec_driver_sql(
                "SELECT content FROM copywritings WHERE content IS NOT NULL"
            )).fetchall()
        }
        existing_covers: set[str] = {
            r[0] for r in (await conn.exec_driver_sql(
                "SELECT file_path FROM covers WHERE file_path IS NOT NULL"
            )).fetchall()
        }
        existing_audios: set[str] = {
            r[0] for r in (await conn.exec_driver_sql(
                "SELECT file_path FROM audios WHERE file_path IS NOT NULL"
            )).fetchall()
        }
        existing_topics: set[str] = {
            r[0] for r in (await conn.exec_driver_sql(
                "SELECT name FROM topics WHERE name IS NOT NULL"
            )).fetchall()
        }

        for m in materials:
            mat_type: str = m.get("type") or ""
            created_at: datetime | None = m.get("created_at")
            updated_at: datetime | None = m.get("updated_at")

            if mat_type == "video":
                file_path: str | None = m.get("path")
                if not file_path or file_path in existing_videos:
                    logger.debug("迁移 004: video material_id={} 已存在或无路径，跳过", m["id"])
                    continue
                await conn.exec_driver_sql(
                    """
                    INSERT INTO videos
                        (name, file_path, file_size, duration, product_id,
                         source_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m.get("name") or "",
                        file_path,
                        m.get("size"),
                        m.get("duration"),
                        m.get("product_id"),
                        "original",
                        created_at,
                        updated_at,
                    ),
                )
                existing_videos.add(file_path)
                counts["videos"] += 1

            elif mat_type == "text":
                content: str | None = m.get("content")
                if not content or content in existing_copywritings:
                    logger.debug("迁移 004: text material_id={} 已存在或无内容，跳过", m["id"])
                    continue
                await conn.exec_driver_sql(
                    """
                    INSERT INTO copywritings
                        (product_id, content, source_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        m.get("product_id"),
                        content,
                        "manual",
                        created_at,
                        updated_at,
                    ),
                )
                existing_copywritings.add(content)
                counts["copywritings"] += 1

            elif mat_type == "cover":
                file_path = m.get("path")
                if not file_path or file_path in existing_covers:
                    logger.debug("迁移 004: cover material_id={} 已存在或无路径，跳过", m["id"])
                    continue
                await conn.exec_driver_sql(
                    """
                    INSERT INTO covers (file_path, file_size, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        file_path,
                        m.get("size"),
                        created_at,
                    ),
                )
                existing_covers.add(file_path)
                counts["covers"] += 1

            elif mat_type == "audio":
                file_path = m.get("path")
                if not file_path or file_path in existing_audios:
                    logger.debug("迁移 004: audio material_id={} 已存在或无路径，跳过", m["id"])
                    continue
                await conn.exec_driver_sql(
                    """
                    INSERT INTO audios (name, file_path, file_size, duration, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        m.get("name") or "",
                        file_path,
                        m.get("size"),
                        m.get("duration"),
                        created_at,
                    ),
                )
                existing_audios.add(file_path)
                counts["audios"] += 1

            elif mat_type == "topic":
                # 话题名优先取 name，回退到 content
                topic_name: str | None = m.get("name") or m.get("content")
                if not topic_name or topic_name in existing_topics:
                    logger.debug("迁移 004: topic material_id={} 已存在或无名称，跳过", m["id"])
                    continue
                await conn.exec_driver_sql(
                    """
                    INSERT INTO topics (name, heat, source, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        topic_name,
                        0,
                        "manual",
                        created_at,
                    ),
                )
                existing_topics.add(topic_name)
                counts["topics"] += 1

            else:
                logger.warning("迁移 004: 未知 material type={}, material_id={}", mat_type, m["id"])

    logger.info(
        "迁移 004 完成 — videos={}, copywritings={}, covers={}, audios={}, topics={}",
        counts["videos"],
        counts["copywritings"],
        counts["covers"],
        counts["audios"],
        counts["topics"],
    )
