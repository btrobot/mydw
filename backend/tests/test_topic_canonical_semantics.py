"""
Phase 6 / PR3: canonical topic semantics baseline tests.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Topic
from services.topic_semantics import merge_task_topic_ids


async def _create_topic(db: AsyncSession, name: str, heat: int = 100) -> Topic:
    topic = Topic(name=name, heat=heat, source="manual")
    db.add(topic)
    await db.flush()
    return topic


def test_merge_task_topic_ids_prefers_explicit_order_then_profile_defaults() -> None:
    merged = merge_task_topic_ids(
        explicit_topic_ids=[5, 3, 5],
        profile_default_topic_ids=[3, 7, 8],
    )

    assert merged == [5, 3, 7, 8]


@pytest.mark.asyncio
async def test_profile_global_topics_round_trip_as_profile_level_defaults(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    t1 = await _create_topic(db_session, "profile_topic_a")
    t2 = await _create_topic(db_session, "profile_topic_b")
    await db_session.commit()

    create_resp = await client.post(
        "/api/profiles",
        json={
            "name": "phase6-profile-topics",
            "composition_mode": "none",
            "global_topic_ids": [t1.id, t2.id],
        },
    )
    assert create_resp.status_code == 201
    payload = create_resp.json()
    assert payload["global_topic_ids"] == [t1.id, t2.id]

    get_resp = await client.get(f"/api/profiles/{payload['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["global_topic_ids"] == [t1.id, t2.id]


@pytest.mark.asyncio
async def test_topic_group_round_trip_remains_named_list_surface_only(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    t1 = await _create_topic(db_session, "group_topic_a")
    t2 = await _create_topic(db_session, "group_topic_b")
    await db_session.commit()

    create_resp = await client.post(
        "/api/topic-groups",
        json={
            "name": "phase6-group",
            "topic_ids": [t1.id, t2.id],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["topic_ids"] == [t1.id, t2.id]
    assert sorted(topic["id"] for topic in created["topics"]) == sorted([t1.id, t2.id])

    update_resp = await client.put(
        f"/api/topic-groups/{created['id']}",
        json={"topic_ids": [t2.id]},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["topic_ids"] == [t2.id]

    list_resp = await client.get("/api/topic-groups")
    assert list_resp.status_code == 200
    assert list_resp.json()["items"][0]["topic_ids"] == [t2.id]
