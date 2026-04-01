"""
账号管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime
from pathlib import Path
from loguru import logger

from models import Account, Task, SystemLog
from models import get_db
from schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountStats,
    AccountLoginRequest, AccountTestRequest
)
from core.browser import browser_manager
from core.dewu_client import get_dewu_client
from utils.crypto import encrypt_data, decrypt_data

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

    # 记录日志
    log = SystemLog(level="INFO", module="account", message=f"创建账号: {account.account_name}")
    db.add(log)
    await db.commit()

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

    # 如果更新了 cookie，进行加密
    if "cookie" in update_data and update_data["cookie"]:
        update_data["cookie"] = encrypt_data(update_data["cookie"])

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

    # 关闭浏览器上下文
    await browser_manager.close_context(account_id)

    await db.delete(account)
    await db.commit()

    logger.info(f"删除账号: {account.account_name}")
    return None


@router.post("/login/{account_id}")
async def login_account(
    account_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    登录账号 - 异步启动登录流程
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 检查是否已有活跃上下文
    existing_context = await browser_manager.get_context(account_id)
    if existing_context:
        # 已有上下文，尝试验证登录状态
        client = await get_dewu_client(account_id)
        client.page = existing_context.pages[0] if existing_context.pages else None
        is_logged_in, msg = await client.check_login_status()

        if is_logged_in:
            # 更新账号状态
            account.status = "active"
            account.last_login = datetime.utcnow()
            await db.commit()

            # 保存存储状态
            storage_state = await browser_manager.save_storage_state(account_id)
            if storage_state:
                account.storage_state = storage_state
                await db.commit()

            return {
                "success": True,
                "message": "账号已登录",
                "status": "active"
            }

    # 启动新的登录流程
    logger.info(f"启动账号 {account.account_name} 登录流程")

    return {
        "success": True,
        "message": "登录流程已启动",
        "status": "pending",
        "tip": "请使用 /accounts/login/screenshot 接口获取登录二维码截图"
    }


@router.get("/login/{account_id}/screenshot")
async def get_login_screenshot(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取登录页面截图
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
        # 创建新的得物客户端
        client = await get_dewu_client(account_id)
        success, msg = await client.login()

        if success:
            # 登录成功，保存状态
            account.status = "active"
            account.last_login = datetime.utcnow()

            # 保存存储状态
            storage_state = await browser_manager.save_storage_state(account_id)
            if storage_state:
                account.storage_state = storage_state

            await db.commit()

            # 记录日志
            log = SystemLog(
                level="INFO",
                module="account",
                message=f"账号登录成功: {account.account_name}"
            )
            db.add(log)
            await db.commit()

            return {
                "success": True,
                "message": "登录成功",
                "status": "active"
            }
        else:
            return {
                "success": False,
                "message": msg,
                "status": account.status
            }

    except Exception as e:
        logger.error(f"登录失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "status": account.status
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

    try:
        # 尝试获取或创建上下文
        context = await browser_manager.get_or_create_context(
            account_id,
            account.storage_state
        )

        if not context or not context.pages:
            return {
                "success": False,
                "status": account.status,
                "message": "无法创建浏览器上下文"
            }

        # 检查登录状态
        page = context.pages[0]
        await page.goto("https://creator.dewu.com", wait_until="networkidle", timeout=30000)

        # 检查是否跳转到登录页
        if "login" in page.url:
            return {
                "success": False,
                "status": "inactive",
                "message": "登录已过期，请重新登录"
            }

        return {
            "success": True,
            "status": "active",
            "last_login": account.last_login,
            "message": "账号正常"
        }

    except Exception as e:
        logger.error(f"测试账号失败: {e}")
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@router.post("/logout/{account_id}")
async def logout_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """登出账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 关闭浏览器上下文
    await browser_manager.close_context(account_id)

    # 清除存储状态
    account.status = "inactive"
    account.storage_state = None
    account.cookie = None

    await db.commit()

    logger.info(f"账号登出: {account.account_name}")
    return {"success": True, "message": "已登出"}
