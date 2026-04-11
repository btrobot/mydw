"""
Phase 6 / PR4: topic relation migration + cutover tests.
"""
from __future__ import annotations

import importlib
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import (
    Account,
    GlobalTopic,
    PublishConfig,
    PublishProfile,
    PublishProfileTopic,
    Task,
    Topic,
    TopicGroup,
    TopicGroupTopic,
    Video,
)


async def _create_topic(db: AsyncSession, name: str, heat: int = 100) -> Topic:
    topic = Topic(name=name, heat=heat, source="manual")
    db.add(topic)
    await db.flush()
    return topic


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"pr4_topic_{suffix}",
        account_name=f"PR4 Topic {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_video(db: AsyncSession, suffix: str) -> Video:
    video = Video(name=f"video_{suffix}.mp4", file_path=f"videos/video_{suffix}.mp4")
    db.add(video)
    await db.flush()
    return video


@pytest.mark.asyncio
async def test_global_topics_api_prefers_relation_rows_over_legacy_json(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    legacy_topic = await _create_topic(db_session, "legacy_global")
    relation_topic = await _create_topic(db_session, "relation_global")
    db_session.add(PublishConfig(name="default", global_topic_ids=json.dumps([legacy_topic.id])))
    await db_session.flush()
    db_session.add(GlobalTopic(topic_id=relation_topic.id, sort_order=0))
    await db_session.commit()

    response = await client.get("/api/topics/global")

    assert response.status_code == 200
    assert response.json()["topic_ids"] == [relation_topic.id]


@pytest.mark.asyncio
async def test_profile_and_group_apis_dual_write_relation_rows_and_legacy_json(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    t1 = await _create_topic(db_session, "dual_write_a")
    t2 = await _create_topic(db_session, "dual_write_b")
    t3 = await _create_topic(db_session, "dual_write_c")
    await db_session.commit()

    profile_resp = await client.post(
        "/api/profiles",
        json={
            "name": "pr4-dual-write-profile",
            "composition_mode": "none",
            "global_topic_ids": [t1.id, t2.id],
        },
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    profile = (
        await db_session.execute(select(PublishProfile).where(PublishProfile.id == profile_id))
    ).scalar_one()
    profile_topics = (
        await db_session.execute(
            select(PublishProfileTopic)
            .where(PublishProfileTopic.profile_id == profile_id)
            .order_by(PublishProfileTopic.sort_order.asc())
        )
    ).scalars().all()
    assert json.loads(profile.global_topic_ids) == [t1.id, t2.id]
    assert [row.topic_id for row in profile_topics] == [t1.id, t2.id]

    update_profile_resp = await client.put(
        f"/api/profiles/{profile_id}",
        json={"global_topic_ids": [t2.id]},
    )
    assert update_profile_resp.status_code == 200
    assert update_profile_resp.json()["global_topic_ids"] == [t2.id]

    list_profile_resp = await client.get("/api/profiles")
    assert list_profile_resp.status_code == 200
    assert list_profile_resp.json()["items"][0]["global_topic_ids"] == [t2.id]

    group_resp = await client.post(
        "/api/topic-groups",
        json={"name": "pr4-dual-write-group", "topic_ids": [t2.id, t3.id]},
    )
    assert group_resp.status_code == 201
    group_id = group_resp.json()["id"]

    group = (
        await db_session.execute(select(TopicGroup).where(TopicGroup.id == group_id))
    ).scalar_one()
    group_topics = (
        await db_session.execute(
            select(TopicGroupTopic)
            .where(TopicGroupTopic.group_id == group_id)
            .order_by(TopicGroupTopic.sort_order.asc())
        )
    ).scalars().all()
    assert json.loads(group.topic_ids) == [t2.id, t3.id]
    assert [row.topic_id for row in group_topics] == [t2.id, t3.id]


@pytest.mark.asyncio
async def test_task_assembly_prefers_relation_backed_profile_topics_when_json_disagrees(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    legacy_topic = await _create_topic(db_session, "legacy_profile_topic")
    relation_topic = await _create_topic(db_session, "relation_profile_topic")
    account = await _create_account(db_session, "assembler")
    video = await _create_video(db_session, "assembler")

    profile = PublishProfile(
        name="pr4-profile-precedence",
        composition_mode="none",
        global_topic_ids=json.dumps([legacy_topic.id]),
    )
    db_session.add(profile)
    await db_session.flush()
    db_session.add(PublishProfileTopic(profile_id=profile.id, topic_id=relation_topic.id, sort_order=0))
    await db_session.commit()

    response = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [video.id],
            "account_ids": [account.id],
            "profile_id": profile.id,
        },
    )

    assert response.status_code == 201
    assert response.json()[0]["topic_ids"] == [relation_topic.id]


@pytest.mark.asyncio
async def test_global_topics_fall_back_to_legacy_json_after_relation_rows_removed(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    t1 = await _create_topic(db_session, "rollback_a")
    t2 = await _create_topic(db_session, "rollback_b")
    await db_session.commit()

    put_resp = await client.put("/api/topics/global", json={"topic_ids": [t1.id, t2.id]})
    assert put_resp.status_code == 200

    await db_session.execute(GlobalTopic.__table__.delete())
    await db_session.commit()

    get_resp = await client.get("/api/topics/global")
    assert get_resp.status_code == 200
    assert get_resp.json()["topic_ids"] == [t1.id, t2.id]


@pytest.mark.asyncio
async def test_topic_relation_migration_backfills_idempotently() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                """
                CREATE TABLE topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(256) NOT NULL UNIQUE
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE publish_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(64) DEFAULT 'default',
                    global_topic_ids TEXT DEFAULT '[]'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE publish_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL UNIQUE,
                    global_topic_ids TEXT DEFAULT '[]'
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TABLE topic_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL UNIQUE,
                    topic_ids TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            await conn.exec_driver_sql("INSERT INTO topics (id, name) VALUES (1, 't1'), (2, 't2'), (3, 't3')")
            await conn.exec_driver_sql(
                "INSERT INTO publish_config (name, global_topic_ids) VALUES ('default', '[1,2,1]')"
            )
            await conn.exec_driver_sql(
                "INSERT INTO publish_profiles (name, global_topic_ids) VALUES ('profile_1', '[2,3]')"
            )
            await conn.exec_driver_sql(
                "INSERT INTO topic_groups (name, topic_ids) VALUES ('group_1', '[3,1]')"
            )

        migration = importlib.import_module("migrations.022_topic_relation_sources")
        await migration.run_migration(engine)
        await migration.run_migration(engine)

        async with engine.begin() as conn:
            global_rows = (
                await conn.exec_driver_sql("SELECT topic_id, sort_order FROM global_topics ORDER BY sort_order, id")
            ).fetchall()
            profile_rows = (
                await conn.exec_driver_sql(
                    "SELECT profile_id, topic_id, sort_order FROM publish_profile_topics ORDER BY profile_id, sort_order, id"
                )
            ).fetchall()
            group_rows = (
                await conn.exec_driver_sql(
                    "SELECT group_id, topic_id, sort_order FROM topic_group_topics ORDER BY group_id, sort_order, id"
                )
            ).fetchall()

        assert global_rows == [(1, 0), (2, 1)]
        assert profile_rows == [(1, 2, 0), (1, 3, 1)]
        assert group_rows == [(1, 3, 0), (1, 1, 1)]
    finally:
        await engine.dispose()
