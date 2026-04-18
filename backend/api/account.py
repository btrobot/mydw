"""
账号管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from typing import List, AsyncGenerator, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import asyncio
import json
import re

from models import Account, Task, SystemLog, PublishLog, PublishExecutionSnapshot
from models import get_db
from schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountStats,
    AccountLoginRequest, AccountTestRequest,
    ConnectionRequest, ConnectionResponse, ConnectionStatusResponse,
    ConnectionStatus, AccountStatus,
    BatchDeleteRequest, BatchDeleteResponse,
    SendCodeRequest, SendCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    HealthCheckResponse,
    BatchHealthCheckRequest, BatchHealthCheckResponse, BatchHealthCheckResultItem,
    BatchHealthCheckStatusResponse,
    PreviewActionResponse, PreviewCloseRequest, PreviewStatusResponse,
)
from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from core.browser import browser_manager, preview_manager
from core.config import settings
from core.dewu_client import get_dewu_client, get_or_create_client, release_client, _active_clients
from utils.crypto import encrypt_data, decrypt_data, mask_phone
from utils.time import utc_day_start_naive, utc_now_naive

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
            "updated_at": utc_now_naive(),
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
            "updated_at": utc_now_naive(),
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
                    yield {"type": "heartbeat", "timestamp": utc_now_naive().isoformat()}
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


@router.post("/", response_model=AccountResponse, status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
    if account_data.phone:
        account.phone_encrypted = encrypt_data(account_data.phone)
    if account_data.tags:
        account.tags = json.dumps(account_data.tags)
    if account_data.remark:
        account.remark = account_data.remark
    db.add(account)
    await db.commit()
    await db.refresh(account)

    # 记录日志
    log = SystemLog(level="INFO", module="account", message=f"创建账号: {account.account_name}")
    db.add(log)
    await db.commit()

    logger.info("创建账号: {} ({})", account.account_name, account.account_id)
    response = AccountResponse.model_validate(account)
    if account.phone_encrypted:
        response.phone_masked = mask_phone(decrypt_data(account.phone_encrypted))
    return response


@router.get("/", response_model=List[AccountResponse], dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def list_accounts(
    status: str = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取账号列表（支持状态过滤、标签筛选、关键词搜索）"""
    query = select(Account)
    if status:
        query = query.where(Account.status == status)
    if tag:
        query = query.where(Account.tags.contains(f'"{tag}"'))
    if search:
        keyword = f"%{search}%"
        query = query.where(
            or_(
                Account.account_name.ilike(keyword),
                Account.account_id.ilike(keyword),
                Account.dewu_nickname.ilike(keyword),
                Account.remark.ilike(keyword),
            )
        )
    query = query.order_by(Account.created_at.desc())

    result = await db.execute(query)
    accounts = result.scalars().all()
    responses = []
    for account in accounts:
        resp = AccountResponse.model_validate(account)
        if account.phone_encrypted:
            resp.phone_masked = mask_phone(decrypt_data(account.phone_encrypted))
        responses.append(resp)
    return responses


@router.get("/stats", response_model=AccountStats, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
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
    today_start = utc_day_start_naive()

    published = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "uploaded",
            Task.updated_at >= today_start
        )
    )
    today_published = published.scalar()

    # 总视频数
    videos = await db.execute(
        select(func.count(Task.id)).where(Task.status == "uploaded")
    )
    total_videos = videos.scalar()

    return AccountStats(
        total_accounts=total_accounts or 0,
        active_accounts=active_accounts or 0,
        today_published=today_published or 0,
        total_videos=total_videos or 0
    )


async def _count_account_references(db: AsyncSession, account_id: int) -> int:
    """统计账号被任务/发布日志/执行快照引用的总次数。"""
    task_count = (
        await db.execute(select(func.count(Task.id)).where(Task.account_id == account_id))
    ).scalar() or 0
    publish_log_count = (
        await db.execute(select(func.count(PublishLog.id)).where(PublishLog.account_id == account_id))
    ).scalar() or 0
    snapshot_count = (
        await db.execute(
            select(func.count(PublishExecutionSnapshot.id)).where(PublishExecutionSnapshot.account_id == account_id)
        )
    ).scalar() or 0
    return int(task_count + publish_log_count + snapshot_count)


@router.post("/batch-delete", response_model=BatchDeleteResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def batch_delete_accounts(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDeleteResponse:
    """批量删除账号。"""
    deleted = 0
    skipped_ids: List[int] = []

    for account_id in data.ids:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            skipped_ids.append(account_id)
            continue

        if await _count_account_references(db, account_id) > 0:
            skipped_ids.append(account_id)
            continue

        try:
            await _cleanup_account_runtime(account_id)
            await db.delete(account)
            await db.commit()
            deleted += 1
        except IntegrityError:
            await db.rollback()
            skipped_ids.append(account_id)

    logger.info("批量删除账号完成: deleted={}, skipped={}", deleted, len(skipped_ids))
    return BatchDeleteResponse(deleted=deleted, skipped=len(skipped_ids), skipped_ids=skipped_ids)


# ============ 批量健康检查 ============

class BatchCheckState:
    """批量检测全局状态（内存中，单例）"""
    def __init__(self):
        self.in_progress: bool = False
        self.progress: int = 0
        self.total: int = 0
        self.current_account_name: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.logs: List[str] = []

    def start(self, total: int) -> None:
        self.in_progress = True
        self.progress = 0
        self.total = total
        self.started_at = utc_now_naive()
        self.current_account_name = None
        self.logs = []

    def add_log(self, msg: str) -> None:
        self.logs.append(msg)

    def finish(self) -> None:
        self.in_progress = False
        self.current_account_name = None

batch_check_state = BatchCheckState()


class _SessionCheckResult:
    """健康检查内部结果"""
    __slots__ = ("is_valid", "error_message")

    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message


async def _check_session_validity(
    account: Account,
    timeout_ms: int = 15000,
) -> _SessionCheckResult:
    """
    共享的 session 有效性检查逻辑。

    创建临时浏览器上下文 -> 导航到 creator.dewu.com -> 通过 URL 判断。
    调用方负责数据库状态更新。
    """
    temp_ctx_id = -account.id
    try:
        context = await browser_manager.create_context(temp_ctx_id, account.storage_state)
        page = await context.new_page()
        try:
            await page.goto("https://creator.dewu.com", timeout=timeout_ms)
            is_valid = "/login" not in page.url
        finally:
            await browser_manager.close_context(temp_ctx_id)
        return _SessionCheckResult(is_valid=is_valid)
    except Exception as e:
        logger.error("账号 {} 健康检查失败: error_type={}", account.id, type(e).__name__)
        return _SessionCheckResult(is_valid=False, error_message=f"检查失败: {type(e).__name__}")


async def _do_single_health_check(
    db: AsyncSession,
    account: Account,
) -> BatchHealthCheckResultItem:
    """执行单个账号的健康检查（供批量检查调用）"""
    previous_status = account.status
    checked_at = utc_now_naive()

    if not account.storage_state:
        return BatchHealthCheckResultItem(
            account_id=account.id,
            account_name=account.account_name,
            previous_status=previous_status,
            current_status=previous_status,
            is_valid=False,
            message="账号未登录",
            checked_at=checked_at,
        )

    result = await _check_session_validity(
        account, timeout_ms=settings.BATCH_HEALTH_CHECK_TIMEOUT * 1000
    )

    if result.error_message:
        return BatchHealthCheckResultItem(
            account_id=account.id,
            account_name=account.account_name,
            previous_status=previous_status,
            current_status=previous_status,
            is_valid=False,
            message=result.error_message,
            checked_at=checked_at,
        )

    now = utc_now_naive()
    session_ttl = timedelta(hours=settings.SESSION_TTL_HOURS)

    if result.is_valid:
        account.last_health_check = now
        account.session_expires_at = now + session_ttl
        current_status = account.status
        msg = "Session 有效"
    else:
        account.status = AccountStatus.SESSION_EXPIRED.value
        current_status = AccountStatus.SESSION_EXPIRED.value
        msg = "Session 已过期"

    await db.commit()

    return BatchHealthCheckResultItem(
        account_id=account.id,
        account_name=account.account_name,
        previous_status=previous_status,
        current_status=current_status,
        is_valid=result.is_valid,
        message=msg,
        checked_at=now,
    )


@router.post("/batch-health-check", response_model=BatchHealthCheckResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def batch_health_check(
    request: BatchHealthCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchHealthCheckResponse:
    """
    批量健康检查 - 串行执行，带间隔和熔断

    默认检测所有非 inactive/disabled 账号。
    连续 3 次非 session 过期错误自动停止。
    """
    if batch_check_state.in_progress:
        raise HTTPException(status_code=409, detail="批量检测正在进行中")

    query = select(Account)
    if request.account_ids:
        query = query.where(Account.id.in_(request.account_ids))
    if request.skip_inactive:
        query = query.where(Account.status.notin_([
            AccountStatus.INACTIVE.value,
            AccountStatus.DISABLED.value,
        ]))
    query = query.order_by(Account.id)

    result = await db.execute(query)
    accounts = list(result.scalars().all())

    if not accounts:
        raise HTTPException(status_code=400, detail="没有可检测的账号")

    if len(accounts) > settings.BATCH_HEALTH_CHECK_MAX_ACCOUNTS:
        accounts = accounts[:settings.BATCH_HEALTH_CHECK_MAX_ACCOUNTS]

    batch_check_state.start(len(accounts))
    started_at = batch_check_state.started_at

    results: List[BatchHealthCheckResultItem] = []
    consecutive_errors = 0
    skipped = 0

    try:
        for account in accounts:
            batch_check_state.current_account_name = account.account_name
            batch_check_state.progress = len(results)

            item = await _do_single_health_check(db, account)
            results.append(item)

            status_icon = "OK" if item.is_valid else "EXPIRED" if "过期" in item.message else "ERROR"
            batch_check_state.add_log(
                f"[{len(results)}/{len(accounts)}] {item.account_name} - {item.message} [{status_icon}]"
            )

            if not item.is_valid and "检查失败" in item.message:
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    logger.warning("批量检查熔断：连续 {} 次错误，停止检测", consecutive_errors)
                    batch_check_state.add_log(
                        f"[!] 连续 {consecutive_errors} 次错误，自动停止检测"
                    )
                    skipped = len(accounts) - len(results)
                    break
            else:
                consecutive_errors = 0

            if request.interval_seconds > 0 and account != accounts[-1]:
                await asyncio.sleep(request.interval_seconds)
    finally:
        batch_check_state.finish()

    completed_at = utc_now_naive()
    valid_count = sum(1 for r in results if r.is_valid)
    expired_count = sum(1 for r in results if not r.is_valid and "过期" in r.message)
    error_count = sum(1 for r in results if not r.is_valid and "失败" in r.message)

    logger.info(
        "批量健康检查完成: total={}, checked={}, valid={}, expired={}, error={}",
        len(accounts), len(results), valid_count, expired_count, error_count
    )

    return BatchHealthCheckResponse(
        total=len(accounts),
        checked=len(results),
        skipped=skipped,
        valid_count=valid_count,
        expired_count=expired_count,
        error_count=error_count,
        results=results,
        started_at=started_at,
        completed_at=completed_at,
    )


@router.get(
    "/batch-health-check/status",
    response_model=BatchHealthCheckStatusResponse,
    dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES,
)
async def batch_health_check_status() -> BatchHealthCheckStatusResponse:
    """获取批量检测进度"""
    return BatchHealthCheckStatusResponse(
        in_progress=batch_check_state.in_progress,
        progress=batch_check_state.progress,
        total=batch_check_state.total,
        current_account_name=batch_check_state.current_account_name,
        started_at=batch_check_state.started_at,
        logs=batch_check_state.logs,
    )


@router.get("/{account_id}", response_model=AccountResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取账号详情"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    response = AccountResponse.model_validate(account)
    if account.phone_encrypted:
        response.phone_masked = mask_phone(decrypt_data(account.phone_encrypted))
    return response


@router.put("/{account_id}", response_model=AccountResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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

    # 处理 tags（需要 JSON 序列化）
    if "tags" in update_data:
        if update_data["tags"] is not None:
            account.tags = json.dumps(update_data["tags"])
        del update_data["tags"]

    # 处理 remark
    if "remark" in update_data:
        if update_data["remark"] is not None:
            account.remark = update_data["remark"]
        del update_data["remark"]

    # 处理 phone（加密后写入 phone_encrypted）
    if "phone" in update_data:
        if update_data["phone"]:
            account.phone_encrypted = encrypt_data(update_data["phone"])
        del update_data["phone"]

    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)

    logger.info("更新账号: {}", account.account_name)
    return account


async def _cleanup_account_runtime(account_id: int) -> None:
    """清理账号相关的浏览器、预览和内存态。"""
    await browser_manager.close_context(account_id)
    release_client(account_id)
    connection_status_manager.clear_status(account_id)

    if preview_manager.is_open and preview_manager.current_account_id == account_id:
        try:
            await preview_manager.close(save_session=False)
        except Exception as e:
            logger.warning("关闭预览浏览器失败，强制清理: error_type={}", type(e).__name__)
            preview_manager._current_account_id = None
            preview_manager._context = None
            preview_manager._page = None
            preview_manager.browser = None
            preview_manager.playwright = None


@router.delete("/{account_id}", status_code=204, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除账号"""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    ref_count = await _count_account_references(db, account_id)
    if ref_count > 0:
        raise HTTPException(status_code=409, detail=f"账号存在 {ref_count} 条关联任务/发布记录，无法删除")

    try:
        await _cleanup_account_runtime(account_id)
        await db.delete(account)
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=409, detail="账号仍存在关联任务或发布记录，无法删除") from error

    logger.info("删除账号: {}", account.account_name)
    return None


@router.post("/{account_id}/health-check", response_model=HealthCheckResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def health_check(
    account_id: int,
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    """
    检查账号 Session 是否仍有效

    创建临时浏览器上下文加载 storage_state，
    导航到 creator.dewu.com，通过 URL 判断 session 是否过期。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.storage_state:
        return HealthCheckResponse(
            success=True,
            is_valid=False,
            message="账号未登录",
        )

    check = await _check_session_validity(account, timeout_ms=15000)

    if check.error_message:
        return HealthCheckResponse(
            success=False,
            is_valid=False,
            message=check.error_message,
        )

    now = utc_now_naive()
    session_ttl = timedelta(hours=settings.SESSION_TTL_HOURS)

    if check.is_valid:
        account.last_health_check = now
        account.session_expires_at = now + session_ttl
        expires_at = account.session_expires_at
        message = "Session 有效"
    else:
        account.status = AccountStatus.SESSION_EXPIRED.value
        expires_at = None
        message = "Session 已过期，请重新登录"

    await db.commit()

    logger.info(
        "账号 {} 健康检查完成: is_valid={}, account_id={}",
        account.account_name, check.is_valid, account_id
    )

    return HealthCheckResponse(
        success=True,
        is_valid=check.is_valid,
        message=message,
        expires_at=expires_at,
    )


@router.get("/preview/status", response_model=PreviewStatusResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def preview_status() -> PreviewStatusResponse:
    """获取当前预览浏览器状态（供前端轮询）"""
    is_open = preview_manager.is_open
    # 活性检查：如果 is_open 但浏览器实际已断开，重置状态
    if is_open and (preview_manager.browser is None or not preview_manager.browser.is_connected()):
        preview_manager._current_account_id = None
        is_open = False
    return PreviewStatusResponse(
        is_open=is_open,
        account_id=preview_manager.current_account_id,
    )


@router.post("/{account_id}/preview", response_model=PreviewActionResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def preview_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
) -> PreviewActionResponse:
    """
    打开账号的 headed 预览浏览器

    加载已登录的得物 session，让用户在可见窗口中查看创作者平台。
    一次只允许一个预览窗口；打开新预览会先关闭已有的。
    """
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.storage_state:
        raise HTTPException(status_code=400, detail="账号尚未登录，无法打开预览")

    try:
        await preview_manager.open(account_id, account.storage_state)
    except Exception as e:
        logger.error("账号 {} 打开预览浏览器失败: error_type={}", account_id, type(e).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail="打开预览浏览器失败")

    logger.info("账号 {} 预览浏览器已打开", account_id)
    return PreviewActionResponse(
        success=True,
        message="预览浏览器已打开",
        is_open=True,
        account_id=account_id,
    )


@router.post(
    "/{account_id}/preview/close",
    response_model=PreviewActionResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def close_preview(
    account_id: int,
    request: PreviewCloseRequest,
    db: AsyncSession = Depends(get_db),
) -> PreviewActionResponse:
    """
    关闭预览浏览器

    可选择保存更新后的 session：若 save_session=True，
    将把最新的 storage_state 加密后写入数据库。
    """
    if not preview_manager.is_open:
        raise HTTPException(status_code=400, detail="当前没有打开的预览浏览器")

    if preview_manager.current_account_id != account_id:
        raise HTTPException(
            status_code=400,
            detail=f"当前预览的账号不是 {account_id}",
        )

    try:
        saved_state = await preview_manager.close(save_session=request.save_session)
    except Exception as e:
        logger.error("账号 {} 关闭预览浏览器失败: error_type={}", account_id, type(e).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail="关闭预览浏览器失败")

    if request.save_session and saved_state:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if account:
            account.storage_state = saved_state
            await db.commit()
            logger.info("账号 {} 预览 session 已保存到数据库", account_id)

    logger.info("账号 {} 预览浏览器已关闭 (save_session={})", account_id, request.save_session)
    return PreviewActionResponse(
        success=True,
        message="预览已关闭",
        is_open=False,
        account_id=None,
    )


@router.post(
    "/connect/{account_id}",
    response_model=ConnectionResponse,
    deprecated=True,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
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
            account.last_login = utc_now_naive()

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



# ============ 两阶段连接端点 ============

@router.post(
    "/connect/{account_id}/send-code",
    response_model=SendCodeResponse,
    status_code=202,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def send_sms_code(
    account_id: int,
    request: SendCodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> SendCodeResponse:
    """
    第一阶段：发送短信验证码

    触发后端在浏览器中打开得物登录页，输入手机号并点击发送验证码按钮。
    后端保持浏览器实例以供 verify 步骤使用。

    浏览器操作为异步后台任务，通过 SSE 推送实际发送状态。
    """
    # 验证账号存在
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 确定实际使用的手机号
    phone = request.phone
    if not phone:
        if account.phone_encrypted:
            phone = decrypt_data(account.phone_encrypted)
        else:
            raise HTTPException(status_code=400, detail="没有存储的手机号，请输入手机号")

    # 验证手机号格式
    if not re.match(r'^1\d{10}$', phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确，必须为11位数字")

    # 检查是否已有进行中的连接（非终态）
    current_status = connection_status_manager.get_status(account_id)
    if current_status:
        terminal_states = {ConnectionStatus.SUCCESS, ConnectionStatus.ERROR, ConnectionStatus.IDLE}
        if current_status["status"] not in terminal_states:
            raise HTTPException(status_code=409, detail="账号正在连接中，请勿重复提交")

    # 更新账号状态为连接中
    account.status = AccountStatus.LOGGING_IN.value
    await db.commit()

    # 同步推送 WAITING_PHONE (progress=10)
    await connection_status_manager.set_status(
        account_id,
        ConnectionStatus.WAITING_PHONE,
        "正在打开浏览器，准备发送验证码",
        10,
    )

    # 后台异步执行浏览器操作
    async def _background_send_code(acc_id: int, phone: str) -> None:
        try:
            client = await get_or_create_client(acc_id)
            # 将本次使用的手机号挂在 client 实例上，供 verify 阶段使用
            client._phone = phone
            send_success, send_message = await client.send_sms_code(phone)
            if send_success:
                await connection_status_manager.set_status(
                    acc_id,
                    ConnectionStatus.CODE_SENT,
                    "验证码已发送，请在5分钟内输入",
                    40,
                )
                logger.info("账号 {} 验证码发送成功", acc_id)
            else:
                await connection_status_manager.set_status(
                    acc_id,
                    ConnectionStatus.ERROR,
                    send_message,
                    0,
                )
                release_client(acc_id)
                # 恢复账号状态——需要新建独立 db session
                from models import get_db as make_db
                async for session in make_db():
                    res = await session.execute(select(Account).where(Account.id == acc_id))
                    acc = res.scalar_one_or_none()
                    if acc:
                        acc.status = AccountStatus.INACTIVE.value
                        await session.commit()
                logger.warning("账号 {} 验证码发送失败: {}", acc_id, send_message)
        except Exception as e:
            logger.error("账号 {} 后台发送验证码异常: {}", acc_id, e, exc_info=True)
            await connection_status_manager.set_status(
                acc_id,
                ConnectionStatus.ERROR,
                f"发送验证码异常: {str(e)}",
                0,
            )
            release_client(acc_id)

    background_tasks.add_task(_background_send_code, account_id, phone)

    return SendCodeResponse(
        success=True,
        message="验证码发送中，请通过 SSE 监听状态",
        status="waiting_phone",
    )


@router.post(
    "/connect/{account_id}/verify",
    response_model=VerifyCodeResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def verify_sms_code(
    account_id: int,
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyCodeResponse:
    """
    第二阶段：验证码登录

    将用户输入的验证码填入浏览器中已打开的登录表单，
    点击登录按钮，等待登录结果，成功后保存加密 session。
    """
    # 验证账号存在
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 检查验证码格式（仅数字）
    if not re.match(r'^\d{4,6}$', request.code):
        raise HTTPException(status_code=400, detail="验证码格式不正确，需为4-6位数字")

    # 检查是否有进行中的连接会话（code_sent 或 waiting_verify）
    current_status = connection_status_manager.get_status(account_id)
    valid_states = {ConnectionStatus.CODE_SENT, ConnectionStatus.WAITING_VERIFY}
    if not current_status or current_status["status"] not in valid_states:
        raise HTTPException(status_code=422, detail="没有进行中的连接会话，请先发送验证码")

    # 获取已持有的 DewuClient 实例
    client = _active_clients.get(account_id)
    if not client:
        raise HTTPException(status_code=422, detail="没有进行中的连接会话，请先发送验证码")

    try:
        # 推送 WAITING_VERIFY (progress=50)
        await connection_status_manager.set_status(
            account_id,
            ConnectionStatus.WAITING_VERIFY,
            "正在提交验证码",
            50,
        )

        # 调用 verify_sms_code — 不传验证码内容到日志
        verify_success, verify_message = await client.verify_sms_code(request.code)

        if verify_success:
            # 推送 VERIFYING (progress=80)
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.VERIFYING,
                "验证码正确，正在保存连接状态",
                80,
            )

            # 保存加密 session
            storage_state = await client.save_login_session()
            if storage_state:
                account.storage_state = storage_state
            else:
                logger.warning("账号 {} 未能保存 storage state", account_id)

            # 保存加密手机号（使用本次登录实际使用的手机号）
            if hasattr(client, '_phone') and client._phone:
                account.phone_encrypted = encrypt_data(client._phone)

            # 更新账号状态
            account.status = AccountStatus.ACTIVE.value
            account.last_login = utc_now_naive()
            await db.commit()

            # 写入系统日志
            log = SystemLog(
                level="INFO",
                module="account",
                message=f"账号连接成功: {account.account_name}",
            )
            db.add(log)
            await db.commit()

            # 推送 SUCCESS (progress=100)
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.SUCCESS,
                "连接成功",
                100,
            )
            release_client(account_id)
            logger.info("账号 {} 连接成功", account.account_name)

            return VerifyCodeResponse(
                success=True,
                message="连接成功",
                status="active",
            )
        else:
            # 业务失败：验证码错误或过期
            await connection_status_manager.set_status(
                account_id,
                ConnectionStatus.ERROR,
                verify_message,
                0,
            )
            account.status = AccountStatus.INACTIVE.value
            await db.commit()
            release_client(account_id)
            logger.warning("账号 {} 验证码验证失败: {}", account.account_name, verify_message)

            return VerifyCodeResponse(
                success=False,
                message=verify_message,
                status="inactive",
            )

    except Exception as e:
        logger.error("账号 {} 验证码登录异常: account_id={}, error_type={}", account.account_name, account_id, type(e).__name__, exc_info=True)

        await connection_status_manager.set_status(
            account_id,
            ConnectionStatus.ERROR,
            "登录过程发生内部错误",
            0,
        )
        account.status = AccountStatus.ERROR.value
        await db.commit()
        release_client(account_id)

        return VerifyCodeResponse(
            success=False,
            message="登录过程发生内部错误",
            status="error",
        )


# ============ 已弃用端点 (向后兼容) ============

@router.post(
    "/login/{account_id}",
    response_model=ConnectionResponse,
    deprecated=True,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def login_account_deprecated(
    account_id: int,
    request: ConnectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}"""
    return await connect_account(account_id, request, background_tasks, db)


@router.get("/connect/{account_id}/stream", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
                    yield f"data: {json.dumps({'message': '连接流程结束', 'final_status': status.value})}\n\n"
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
@router.get("/login/{account_id}/stream", deprecated=True, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def login_status_stream_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/stream"""
    return await connection_status_stream(account_id, db)


@router.get(
    "/connect/{account_id}/status",
    response_model=ConnectionStatusResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
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
@router.get(
    "/login/{account_id}/status",
    response_model=ConnectionStatusResponse,
    deprecated=True,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def get_login_status_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/status"""
    return await get_connection_status(account_id, db)


@router.post("/connect/{account_id}/export", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
@router.post("/login/{account_id}/export", deprecated=True, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def export_session_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}/export"""
    return await export_session(account_id, db)


@router.post("/connect/{account_id}/import", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
@router.post("/login/{account_id}/import", deprecated=True, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def import_session_deprecated(
    account_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /connect/{account_id}/import"""
    return await import_session(account_id, request, db)


@router.get("/connect/{account_id}/screenshot", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
@router.get("/login/{account_id}/screenshot", deprecated=True, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def get_login_screenshot_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 GET /connect/{account_id}/screenshot"""
    return await get_connection_screenshot(account_id, db)


@router.post("/test/{account_id}", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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
        logger.error("测试账号失败: {}", e)
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@router.post("/disconnect/{account_id}", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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

    # 释放 DewuClient 实例（如果两阶段流程中被取消）
    release_client(account_id)

    # 清除 SSE 状态
    connection_status_manager.clear_status(account_id)

    # 清除存储状态
    account.status = "inactive"
    account.storage_state = None
    account.cookie = None

    await db.commit()

    logger.info("账号连接已断开: {}", account.account_name)
    return {"success": True, "message": "已断开连接"}


# 已弃用端点 (向后兼容)
@router.post("/logout/{account_id}", deprecated=True, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def logout_account_deprecated(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """已弃用: 请使用 POST /disconnect/{account_id}"""
    return await disconnect_account(account_id, db)
