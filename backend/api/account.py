"""
账号管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from loguru import logger

from models import Account, Task
from models import get_db
from schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountStats,
    AccountLoginRequest, AccountTestRequest
)

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建账号"""
    # 检查账号是否已存在
    result = await db.execute(
        select(Account).where(Account.account_id == account_data.account_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="账号已存在")

    account = Account(
        account_id=account_data.account_id,
        account_name=account_data.account_name,
        status="inactive"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    logger.info(f"创建账号: {account.account_name} ({account.account_id})")
    return account


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取账号列表"""
    query = select(Account)
    if status:
        query = query.where(Account.status == status)
    query = query.order_by(Account.created_at.desc())

    result = await db.execute(query)
    accounts = result.scalars().all()
    return accounts


@router.get("/stats", response_model=AccountStats)
async def get_account_stats(db: AsyncSession = Depends(get_db)):
    """获取账号统计"""
    # 总账号数
    total = await db.execute(select(func.count(Account.id)))
    total_accounts = total.scalar()

    # 活跃账号数
    active = await db.execute(
        select(func.count(Account.id)).where(Account.status == "active")
    )
    active_accounts = active.scalar()

    # 今日发布数
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    published = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "success",
            Task.updated_at >= today_start
        )
    )
    today_published = published.scalar()

    # 总视频数
    videos = await db.execute(
        select(func.count(Task.id)).where(Task.status == "success")
    )
    total_videos = videos.scalar()

    return AccountStats(
        total_accounts=total_accounts or 0,
        active_accounts=active_accounts or 0,
        today_published=today_published or 0,
        total_videos=total_videos or 0
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取账号详情"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 更新字段
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)

    logger.info(f"更新账号: {account.account_name}")
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    await db.delete(account)
    await db.commit()

    logger.info(f"删除账号: {account.account_name}")
    return None


@router.post("/login")
async def login_account(
    request: AccountLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """登录账号 - 启动浏览器让用户登录"""
    result = await db.execute(
        select(Account).where(Account.account_id == request.account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # TODO: 启动 Playwright 浏览器让用户登录
    # 登录成功后更新 cookie 和状态

    logger.info(f"开始登录账号: {account.account_name}")

    return {
        "success": True,
        "message": "请在新窗口中完成登录",
        "account_id": account.id
    }


@router.post("/test/{account_id}")
async def test_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试账号状态"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # TODO: 使用 Playwright 测试登录状态

    return {
        "success": True,
        "status": account.status,
        "last_login": account.last_login
    }
