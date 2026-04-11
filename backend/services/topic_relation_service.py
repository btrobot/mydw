"""
Topic relation canonical source helpers.

Phase 6 / PR4:
- read relation-table canonical sources first
- keep legacy JSON columns dual-written for rollback safety
"""
from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    GlobalTopic,
    PublishConfig,
    PublishProfile,
    PublishProfileTopic,
    Topic,
    TopicGroup,
    TopicGroupTopic,
)


def normalize_topic_ids(topic_ids: Iterable[int] | None) -> list[int]:
    ordered: list[int] = []
    seen: set[int] = set()
    for value in topic_ids or []:
        if isinstance(value, int) and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def parse_legacy_topic_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return normalize_topic_ids(parsed if isinstance(parsed, list) else [])


async def get_global_topic_ids(db: AsyncSession) -> list[int]:
    result = await db.execute(
        select(GlobalTopic).order_by(GlobalTopic.sort_order.asc(), GlobalTopic.id.asc())
    )
    rows = result.scalars().all()
    if rows:
        return [row.topic_id for row in rows]

    cfg_result = await db.execute(select(PublishConfig).limit(1))
    config = cfg_result.scalars().first()
    return parse_legacy_topic_ids(config.global_topic_ids if config else None)


async def get_profile_topic_ids(db: AsyncSession, profile: PublishProfile | None) -> list[int]:
    if profile is None:
        return []

    result = await db.execute(
        select(PublishProfileTopic)
        .where(PublishProfileTopic.profile_id == profile.id)
        .order_by(PublishProfileTopic.sort_order.asc(), PublishProfileTopic.id.asc())
    )
    rows = result.scalars().all()
    if rows:
        return [row.topic_id for row in rows]

    return parse_legacy_topic_ids(profile.global_topic_ids)


async def get_topic_group_topic_ids(db: AsyncSession, group: TopicGroup | None) -> list[int]:
    if group is None:
        return []

    result = await db.execute(
        select(TopicGroupTopic)
        .where(TopicGroupTopic.group_id == group.id)
        .order_by(TopicGroupTopic.sort_order.asc(), TopicGroupTopic.id.asc())
    )
    rows = result.scalars().all()
    if rows:
        return [row.topic_id for row in rows]

    return parse_legacy_topic_ids(group.topic_ids)


async def sync_global_topic_ids(db: AsyncSession, topic_ids: Iterable[int]) -> list[int]:
    normalized = normalize_topic_ids(topic_ids)

    await db.execute(delete(GlobalTopic))
    for order, topic_id in enumerate(normalized):
        db.add(GlobalTopic(topic_id=topic_id, sort_order=order))

    cfg_result = await db.execute(select(PublishConfig).limit(1))
    config = cfg_result.scalars().first()
    if not config:
        config = PublishConfig()
        db.add(config)
        await db.flush()
    config.global_topic_ids = json.dumps(normalized)

    return normalized


async def sync_profile_topic_ids(
    db: AsyncSession,
    profile: PublishProfile,
    topic_ids: Iterable[int],
) -> list[int]:
    normalized = normalize_topic_ids(topic_ids)

    await db.execute(
        delete(PublishProfileTopic).where(PublishProfileTopic.profile_id == profile.id)
    )
    for order, topic_id in enumerate(normalized):
        db.add(PublishProfileTopic(profile_id=profile.id, topic_id=topic_id, sort_order=order))

    profile.global_topic_ids = json.dumps(normalized)
    return normalized


async def sync_topic_group_topic_ids(
    db: AsyncSession,
    group: TopicGroup,
    topic_ids: Iterable[int],
) -> list[int]:
    normalized = normalize_topic_ids(topic_ids)

    await db.execute(
        delete(TopicGroupTopic).where(TopicGroupTopic.group_id == group.id)
    )
    for order, topic_id in enumerate(normalized):
        db.add(TopicGroupTopic(group_id=group.id, topic_id=topic_id, sort_order=order))

    group.topic_ids = json.dumps(normalized)
    return normalized


async def get_topics_by_ids(db: AsyncSession, topic_ids: Iterable[int]) -> list[Topic]:
    normalized = normalize_topic_ids(topic_ids)
    if not normalized:
        return []

    rows = (await db.execute(select(Topic).where(Topic.id.in_(normalized)))).scalars().all()
    topic_map = {topic.id: topic for topic in rows}
    return [topic_map[topic_id] for topic_id in normalized if topic_id in topic_map]
