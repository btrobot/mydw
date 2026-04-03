"""
账号管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, AsyncGenerator, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from loguru import logger
import asyncio
import json

from models import Account, Task, SystemLog
from models import get_db
from schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountStats,
    AccountLoginRequest, AccountTestRequest,
    ConnectionRequest, ConnectionResponse, ConnectionStatusResponse,
    ConnectionStatus, AccountStatus
)
from core.browser import browser_manager
from core.dewu_client import get_dewu_client
from utils.crypto import encrypt_data, decrypt_data

router = APIRouter()


# ============ 连接状态管理器 (事件驱动) ============

class ConnectionStatusManager:
    """
    得物账号连接状态管理器 - 事件驱动版本

    使用 asyncio.Queue 实现事件驱动的订阅模式，
    SSE 端点通过订阅状态变化实现实时推送。

    状态结构: {
        "status": ConnectionStatus,
        "message": str,
        "progress": int,
        "updated_at": datetime,
        "event": asyncio.Event  # 用于通知状态变化
    }
    """

    def __init__(self):
        # 状态存储: account_id -> status_data
        self._status: Dict[int, Dict[str, Any]] = {}
        # 订阅队列: account_id -> asyncio.Queue
        self._queues: Dict[int, asyncio.Queue] = {}
        # 订阅者锁
        self._lock = asyncio.Lock()

    async def set_status(
        self,
        account_id: int,
        status: ConnectionStatus,
        message: str,
        progress: int = 0
    ) -> None:
        """
        设置连接状态并通知所有订阅者

        Args:
            account_id: 账号ID
            status: 连接状态枚举
            message: 状态消息
            progress: 进度百分比 (0-100)
        """
        # 获取或创建事件
        event = self._status.get(account_id, {}).get("event")
        if event is None:
            event = asyncio.Event()

        # 更新状态
        self._status[account_id] = {
            "status": status,
            "message": message,
            "progress": progress,
            "updated_at": datetime.utcnow(),
            "event": event
        }

        logger.debug(
            "连接状态更新: account_id={}, status={}, message={}, progress={}",
            account_id, status.value, message, progress
        )

        # 通知所有订阅者
        await self._notify_subscribers(account_id)

    def set_status_sync(
        self,
        account_id: int,
        status: ConnectionStatus,
        message: str,
        progress: int = 0
    ) -> None:
        """
        同步设置连接状态（用于同步上下文）

        Args:
            account_id: 账号ID
            status: 连接状态枚举
            message: 状态消息
            progress: 进度百分比 (0-100)
        """
        # 获取或创建事件
        event = self._status.get(account_id, {}).get("event")
        if event is None:
            event = asyncio.Event()

        # 更新状态
        self._status[account_id] = {
            "status": status,
            "message": message,
            "progress": progress,
            "updated_at": datetime.utcnow(),
            "event": event
        }

        logger.debug(
            "连接状态更新(SYNC): account_id={}, status={}, message={}",
            account_id, status.value, message
        )

        # 通知所有订阅者
        event.set()

    def get_status(self, account_id: int) -> Optional[Dict[str, Any]]:
        """获取连接状态"""
        return self._status.get(account_id)

    def clear_status(self, account_id: int) -> None:
        """清除连接状态"""
        if account_id in self._status:
            del self._status[account_id]
            logger.debug("连接状态已清除: account_id={}", account_id)

    async def subscribe(self, account_id: int) -> AsyncGenerator[Dict[str, Any], None]:
        """
        订阅账号状态变化

        Yields:
            状态更新数据字典

        Example:
            async for status in status_manager.subscribe(account_id):
                await sse.send(status)
        """
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            self._queues[account_id] = queue

        logger.debug("SSE 订阅状态: account_id={}", account_id)

        try:
            # 发送初始状态（如果存在）
            current = self._status.get(account_id)
            if current:
                yield {
                    "status": current["status"],
                    "message": current["message"],
                    "progress": current["progress"],
                    "timestamp": current["updated_at"].isoformat()
                }

            # 持续接收状态更新直到取消
            while True:
                try:
                    # 使用 wait_for 实现带超时的等待
                    status_data = await asyncio.wait_for(
                        queue.get(),
                        timeout=30.0  # 30秒超时发送心跳
                    )
                    yield status_data
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
                except asyncio.CancelledError:
                    break
        finally:
            # 清理订阅
            async with self._lock:
                if account_id in self._queues:
                    del self._queues[account_id]
            logger.debug("SSE 取消订阅: account_id={}", account_id)

    async def _notify_subscribers(self, account_id: int) -> None:
        """通知所有订阅者状态变化"""
        status_data = self._status.get(account_id)
        if not status_data:
            return

        # 构造通知数据
        notification = {
            "status": status_data["status"],
            "message": status_data["message"],
            "progress": status_data["progress"],
            "timestamp": status_data["updated_at"].isoformat()
        }

        # 通知所有队列
        async with self._lock:
            queue = self._queues.get(account_id)
            if queue:
                try:
                    queue.put_nowait(notification)
                except Exception as e:
                    logger.warning("通知订阅者失败: account_id={}, error={}", account_id, e)


# 全局连接状态管理器实例
connection_status_manager = ConnectionStatusManager()


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


@router.post("/connect/{account_id}", response_model=ConnectionResponse)
async def connect_account(
    account_id: int,
    request: ConnectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    连接得物账号 - 手机验证码方式

    执行完整的连接流程：
    1. 打开登录页
    2. 勾选协议
    3. 输入手机号
    4. 点击发送验证码
    5. 输入验证码
    6. 点击登录
    7. 检测登录结果
    8. 保存 storage state

    同时通过 connection_status_manager 推送 SSE 状态。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    logger.info("账号 {} ({}) 开始连接流程", account.account_name, account_id)

    # 更新账号状态为连接中
    account.status = AccountStatus.LOGGING_IN.value
    await db.commit()

    try:
        # 状态1: 等待输入手机号 -> 正在发送验证码
        await connection_status_manager.set_status(
            account_id,
            ConnectionStatus.WAITING_PHONE,
            "等待输入手机号",
            10
        )

        # 创建得物客户端
        client = await get_dewu_client(account_id)

        # 如果只有手机号（发送验证码请求）
        if not request.code or request.code == "":
            # 状态2: 验证码已发送
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.CODE_SENT,
                "验证码已发送，请在5分钟内输入",
                40
            )
            return ConnectionResponse(
                success=True,
                message="验证码已发送",
                status="logging_in"
            )

        # 状态3: 等待验证
        await connection_status_manager.set_status(
            account_id,
            ConnectionStatus.WAITING_VERIFY,
            "正在验证验证码",
            50
        )

        # 执行手机验证码登录
        success, message = await client.login_with_sms(request.phone, request.code)

        if success:
            # 状态4: 正在保存会话
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.VERIFYING,
                "正在保存连接状态",
                80
            )

            # 连接成功，保存状态
            account.status = AccountStatus.ACTIVE.value
            account.last_login = datetime.utcnow()

            # 保存 storage state
            storage_state = await client.save_login_session()
            if storage_state:
                account.storage_state = storage_state
            else:
                logger.warning("账号 {} 未能保存 storage state", account_id)

            await db.commit()

            # 记录日志
            log = SystemLog(
                level="INFO",
                module="account",
                message=f"账号连接成功: {account.account_name}"
            )
            db.add(log)
            await db.commit()

            # 状态5: 连接成功
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.SUCCESS,
                "连接成功",
                100
            )

            logger.info("账号 {} 连接成功", account.account_name)

            return ConnectionResponse(
                success=True,
                message="连接成功",
                status="active",
                storage_state=storage_state
            )
        else:
            # 连接失败
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.ERROR,
                message,
                0
            )

            # 恢复账号状态
            account.status = AccountStatus.INACTIVE.value
            await db.commit()

            logger.warning("账号 {} 连接失败: {}", account.account_name, message)

            return ConnectionResponse(
                success=False,
                message=message,
                status="inactive"
            )

    except Exception as e:
        logger.error("账号 {} 连接异常: {}", account.account_name, e, exc_info=True)

        # 更新状态为错误
        await connection_status_manager.set_status(
            account_id,
            ConnectionStatus.ERROR,
            f"连接异常: {str(e)}",
            0
        )

        # 恢复账号状态
        account.status = AccountStatus.ERROR.value
        await db.commit()

        return ConnectionResponse(
            success=False,
            message=f"连接异常: {str(e)}",
            status="error"
        )


# ============ 已弃用端点 (向后兼容) ============

@router.post("/login/{account_id}", response_model=ConnectionResponse, deprecated=True)
async def login_account_deprecated(
    account_id: int,
    request: ConnectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}"""
    return await connect_account(account_id, request, background_tasks, db)


@router.get("/connect/{account_id}/stream")
async def connection_status_stream(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    SSE 流式推送连接状态 (事件驱动模式)

    端点: GET /api/accounts/connect/{account_id}/stream

    前端需先调用 POST /api/accounts/connect/{account_id} 触发连接流程，
    此端点订阅状态变化并实时推送。

    事件格式:
    - event: status_update
    - data: {"status": "waiting_verify", "message": "验证码已发送", "progress": 50, "timestamp": "..."}

    状态值 (ConnectionStatus):
    - idle: 初始状态
    - waiting_phone: 等待输入手机号
    - code_sent: 验证码已发送
    - waiting_verify: 等待验证
    - verifying: 验证中
    - success: 连接成功
    - error: 连接失败

    超时: 30秒无状态变化发送心跳，保持连接
    """
    # 验证账号存在
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        async def error_generator() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'status': 'error', 'message': '账号不存在'})}\n\n"
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    logger.info("SSE 订阅连接状态: account_id={}, account_name={}", account_id, account.account_name)

    async def event_generator() -> AsyncGenerator[str, None]:
        """
        SSE 事件生成器

        通过订阅 connection_status_manager 的状态变化实现实时推送。
        """
        try:
            # 持续订阅状态变化
            async for status_data in connection_status_manager.subscribe(account_id):
                # 检查是否是心跳
                if status_data.get("type") == "heartbeat":
                    yield f": heartbeat\n\n"
                    continue

                # 发送状态更新事件
                yield f"event: status_update\n"
                yield f"data: {json.dumps(status_data)}\n\n"

                # 如果是终态 (success/error)，发送完成事件并退出
                status = status_data.get("status")
                if status in [ConnectionStatus.SUCCESS, ConnectionStatus.ERROR]:
                    yield f"event: done\n"
                    yield f"data: {json.dumps({'message': '连接流程结束', 'final_status': status})}\n\n"
                    break

        except asyncio.CancelledError:
            logger.info("SSE 连接已断开: account_id={}", account_id)
        except Exception as e:
            logger.error("SSE 发生错误: account_id={}, error={}", account_id, e, exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
        finally:
            # 清理状态
            connection_status_manager.clear_status(account_id)
            logger.debug("SSE 连接清理完成: account_id={}", account_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


# 已弃用端点 (向后兼容)
@router.get("/login/{account_id}/stream", deprecated=True)
async def login_status_stream_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/stream"""
    return await connection_status_stream(account_id, db)


@router.get("/connect/{account_id}/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取得物账号连接状态

    检查账号是否已连接：
    1. 如果有活跃的浏览器上下文，检查页面 URL
    2. 如果没有上下文但有 storage state，尝试验证
    3. 返回详细的连接状态信息
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
        # 检查是否有活跃的浏览器上下文
        context = await browser_manager.get_context(account_id)

        if context and context.pages:
            page = context.pages[0]
            current_url = page.url

            # URL 检查：是否在登录页
            if "login" not in current_url.lower():
                return ConnectionStatusResponse(
                    is_connected=True,
                    status=ConnectionStatus.SUCCESS,
                    last_login=account.last_login,
                    message="账号已连接"
                )
            else:
                return ConnectionStatusResponse(
                    is_connected=False,
                    status=ConnectionStatus.ERROR,
                    last_login=account.last_login,
                    message="Session 已过期，需要重新连接"
                )

        # 检查是否有存储的 session
        if account.storage_state:
            return ConnectionStatusResponse(
                is_connected=False,
                status=ConnectionStatus.IDLE,
                last_login=account.last_login,
                message="有保存的 Session，但浏览器未初始化"
            )

        # 无 session
        return ConnectionStatusResponse(
            is_connected=False,
            status=ConnectionStatus.IDLE,
            last_login=account.last_login,
            message="账号未连接"
        )

    except Exception as e:
        logger.error("检查账号 {} 连接状态失败: {}", account.account_name, e, exc_info=True)
        return ConnectionStatusResponse(
            is_connected=False,
            status=ConnectionStatus.ERROR,
            last_login=account.last_login,
            message=f"检查失败: {str(e)}"
        )


# 已弃用端点 (向后兼容)
@router.get("/login/{account_id}/status", response_model=ConnectionStatusResponse, deprecated=True)
async def get_login_status_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/status"""
    return await get_connection_status(account_id, db)


@router.post("/connect/{account_id}/export")
async def export_session(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    导出账号的连接会话

    将加密后的 storage state 返回给客户端。
    用于备份或迁移账号连接状态。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 检查是否有存储状态
    if not account.storage_state:
        return {
            "success": False,
            "message": "账号没有保存的连接会话"
        }

    return {
        "success": True,
        "message": "连接会话导出成功",
        "storage_state": account.storage_state
    }


# 已弃用端点 (向后兼容)
@router.post("/login/{account_id}/export", deprecated=True)
async def export_session_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}/export"""
    return await export_session(account_id, db)


@router.post("/connect/{account_id}/import")
async def import_session(
    account_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    导入账号的连接会话

    接收加密后的 storage state 并保存到数据库。
    用于恢复或迁移账号连接状态。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    storage_state = request.get("storage_state")
    if not storage_state:
        raise HTTPException(status_code=400, detail="缺少 storage_state 参数")

    # 保存到数据库
    account.storage_state = storage_state
    await db.commit()

    logger.info("账号 {} 连接会话已导入", account.account_name)

    return {
        "success": True,
        "message": "连接会话导入成功"
    }


# 已弃用端点 (向后兼容)
@router.post("/login/{account_id}/import", deprecated=True)
async def import_session_deprecated(
    account_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}/import"""
    return await import_session(account_id, request, db)


@router.get("/connect/{account_id}/screenshot")
async def get_connection_screenshot(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取得物登录页面截图（调试用）

    打开登录页面并截图，用于调试连接问题。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
        # 创建新的得物客户端
        client = await get_dewu_client(account_id)

        # 探索登录页面
        screenshot_path = f"logs/login_debug_{account_id}.png"

        if not client.page:
            client.page = await browser_manager.new_page(account_id)

        if client.page:
            # 访问登录页面
            await client.page.goto(client.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            await client.page.wait_for_timeout(2000)

            # 截图
            await client.page.screenshot(path=screenshot_path, full_page=True)
            logger.info("账号 {} 登录页面截图已保存: {}", account.account_name, screenshot_path)

            return {
                "success": True,
                "message": "截图已保存",
                "screenshot_path": screenshot_path,
                "url": client.page.url
            }
        else:
            return {
                "success": False,
                "message": "无法创建浏览器页面"
            }

    except Exception as e:
        logger.error("账号 {} 获取登录截图失败: {}", account.account_name, e, exc_info=True)
        return {
            "success": False,
            "message": str(e)
        }


# 已弃用端点 (向后兼容)
@router.get("/login/{account_id}/screenshot", deprecated=True)
async def get_login_screenshot_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/screenshot"""
    return await get_connection_screenshot(account_id, db)


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
                "message": "登录已过期，请重新连接"
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


@router.post("/disconnect/{account_id}")
async def disconnect_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """断开账号连接"""
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

    logger.info(f"账号连接已断开: {account.account_name}")
    return {"success": True, "message": "已断开连接"}


# 已弃用端点 (向后兼容)
@router.post("/logout/{account_id}", deprecated=True)
async def logout_account_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /disconnect/{account_id}"""
    return await disconnect_account(account_id, db)
