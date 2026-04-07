"""
SP3-11: 任务编排集成测试

测试 POST /api/tasks/assemble 端点，覆盖：
- 基础组装（2 Video + 2 Account）
- round_robin 分配策略（3 Video + 2 Account）
- 文案自动匹配（同 product_id）
- FK 字段创建任务
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, Video, Copywriting, Product


# ============ 辅助函数 ============

async def _create_account(db: AsyncSession, suffix: str) -> Account:
    account = Account(
        account_id=f"acct_{suffix}",
        account_name=f"Account {suffix}",
        status="active",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_video(
    db: AsyncSession,
    suffix: str,
    product_id: int | None = None,
) -> Video:
    video = Video(
        name=f"video_{suffix}.mp4",
        file_path=f"videos/video_{suffix}.mp4",
        product_id=product_id,
    )
    db.add(video)
    await db.flush()
    return video


async def _create_product(db: AsyncSession, name: str) -> Product:
    product = Product(name=name)
    db.add(product)
    await db.flush()
    return product


async def _create_copywriting(
    db: AsyncSession,
    content: str,
    product_id: int | None = None,
) -> Copywriting:
    cw = Copywriting(content=content, product_id=product_id)
    db.add(cw)
    await db.flush()
    return cw


async def _get_all_tasks(client: AsyncClient) -> list[dict]:
    """GET /api/tasks/ 使用 selectinload，不触发 BUG-001。"""
    resp = await client.get("/api/tasks/")
    assert resp.status_code == 200
    return resp.json()["items"]


# ============ 测试用例 ============

@pytest.mark.asyncio
async def test_assemble_tasks(client: AsyncClient, db_session: AsyncSession) -> None:
    """2 Video + 2 Account → 创建 2 个 task，video_id 正确填充。"""
    acct1 = await _create_account(db_session, "a1")
    acct2 = await _create_account(db_session, "a2")
    vid1 = await _create_video(db_session, "v1")
    vid2 = await _create_video(db_session, "v2")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid1.id, vid2.id],
            "account_ids": [acct1.id, acct2.id],
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 2
    video_ids_created = {t["video_id"] for t in tasks}
    assert video_ids_created == {vid1.id, vid2.id}


@pytest.mark.asyncio
async def test_distribute_round_robin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """3 Video + 2 Account，round_robin → account 分配顺序为 [acct1, acct2, acct1]。"""
    acct1 = await _create_account(db_session, "rr_a1")
    acct2 = await _create_account(db_session, "rr_a2")
    vid1 = await _create_video(db_session, "rr_v1")
    vid2 = await _create_video(db_session, "rr_v2")
    vid3 = await _create_video(db_session, "rr_v3")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid1.id, vid2.id, vid3.id],
            "account_ids": [acct1.id, acct2.id],
            "strategy": "round_robin",
        },
    )
    assert resp.status_code == 201
    tasks = sorted(resp.json(), key=lambda t: t["video_id"])
    assert len(tasks) == 3
    expected_accounts = [acct1.id, acct2.id, acct1.id]
    actual_accounts = [t["account_id"] for t in tasks]
    assert actual_accounts == expected_accounts


@pytest.mark.asyncio
async def test_assemble_with_copywriting(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Video + Copywriting 同 product_id → task.copywriting_id 自动匹配。"""
    product = await _create_product(db_session, "prod_cw_test")
    acct = await _create_account(db_session, "cw_a1")
    vid = await _create_video(db_session, "cw_v1", product_id=product.id)
    cw = await _create_copywriting(db_session, "测试文案内容", product_id=product.id)
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/assemble",
        json={
            "video_ids": [vid.id],
            "account_ids": [acct.id],
            "copywriting_mode": "auto_match",
        },
    )
    assert resp.status_code == 201
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["copywriting_id"] == cw.id


@pytest.mark.asyncio
async def test_create_task_with_fk(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """通过 FK 字段 (video_id) 创建 task，GET /api/tasks 仍可返回。"""
    acct = await _create_account(db_session, "bc_a1")
    vid = await _create_video(db_session, "bc_v1")
    await db_session.commit()

    resp = await client.post(
        "/api/tasks/",
        json={
            "account_id": acct.id,
            "video_id": vid.id,
        },
    )
    assert resp.status_code == 201

    tasks = await _get_all_tasks(client)
    assert len(tasks) == 1
    assert tasks[0]["video_id"] == vid.id
    assert tasks[0]["account_id"] == acct.id
