"""
SP4-07: 话题增强集成测试

覆盖：
- test_global_topics_set_and_get   — PUT /api/topics/global 设置3个话题 → GET 验证返回
- test_global_topics_empty         — 设置空列表 → 验证返回空
- test_assemble_with_global_topics — 全局话题 → POST /api/tasks/assemble → task.topic_ids 包含全局话题
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, Topic, Video


# ============ 辅助函数 ============

async def _create_topic(db: AsyncSession, name: str, heat: int = 100) -> Topic:
    topic = Topic(name=name, heat=heat, source="manual")
    db.add(topic)
    await db.flush()
    return topic


async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"acct_{suffix}",
        account_name=f"Account {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_video(db: AsyncSession, suffix: str) -> Video:
    video = Video(
        name=f"video_{suffix}.mp4",
        file_path=f"videos/video_{suffix}.mp4",
    )
    db.add(video)
    await db.flush()
    return video


# ============ 测试用例 ============

@pytest.mark.asyncio
async def test_global_topics_set_and_get(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PUT /api/topics/global 设置3个话题ID → GET /api/topics/global 验证返回一致。"""
    t1 = await _create_topic(db_session, "话题A")
    t2 = await _create_topic(db_session, "话题B")
    t3 = await _create_topic(db_session, "话题C")
    await db_session.commit()

    topic_ids = [t1.id, t2.id, t3.id]

    put_resp = await client.put(
        "/api/topics/global",
        json={"topic_ids": topic_ids},
    )
    assert put_resp.status_code == 200
    put_data = put_resp.json()
    assert sorted(put_data["topic_ids"]) == sorted(topic_ids)

    get_resp = await client.get("/api/topics/global")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert sorted(get_data["topic_ids"]) == sorted(topic_ids)
    assert len(get_data["topics"]) == 3


@pytest.mark.asyncio
async def test_global_topics_empty(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """设置空列表 → GET /api/topics/global 返回空。"""
    # 先设置一些话题，再清空
    t1 = await _create_topic(db_session, "临时话题X")
    await db_session.commit()

    await client.put("/api/topics/global", json={"topic_ids": [t1.id]})

    put_resp = await client.put("/api/topics/global", json={"topic_ids": []})
    assert put_resp.status_code == 200
    assert put_resp.json()["topic_ids"] == []

    get_resp = await client.get("/api/topics/global")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["topic_ids"] == []
    assert get_data["topics"] == []


@pytest.mark.asyncio
async def test_assemble_with_global_topics(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """设置全局话题 → POST /api/tasks/assemble → GET /api/tasks 验证 task.topic_ids 包含全局话题。"""
    t1 = await _create_topic(db_session, "全局话题1")
    t2 = await _create_topic(db_session, "全局话题2")
    acct = await _create_account(db_session, "gt_a1")
    vid = await _create_video(db_session, "gt_v1")
    await db_session.commit()

    # 设置全局话题
    put_resp = await client.put(
        "/api/topics/global",
        json={"topic_ids": [t1.id, t2.id]},
    )
    assert put_resp.status_code == 200

    # 组装任务
    assemble_resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid.id],
            "account_ids": [acct.id],
        },
    )
    assert assemble_resp.status_code == 201
    tasks = assemble_resp.json()
    assert len(tasks) == 1

    # 通过 GET /api/tasks 验证 topic_ids
    list_resp = await client.get("/api/tasks/")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert sorted(items[0]["topic_ids"]) == sorted([t1.id, t2.id])
