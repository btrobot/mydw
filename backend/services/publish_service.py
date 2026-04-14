"""
任务发布服务
"""
from typing import Awaitable, Callable, Optional
from datetime import datetime, time
from zoneinfo import ZoneInfo
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Task, Account, ScheduleConfig
from core.browser import browser_manager
from core.auth_dependencies import (
    get_runtime_auth_failure_reason,
    is_runtime_hard_stop_state,
    require_active_service_session,
)
from core.dewu_client import get_dewu_client
from schemas.auth import LocalAuthSessionSummary
from services.task_service import TaskService
from services.task_execution_semantics import (
    PublishabilityError,
    resolve_publish_execution_view,
)


class PublishService:
    """发布服务"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self.current_task_id: Optional[int] = None
        self._auth_summary = auth_summary

    async def _get_schedule_config(self) -> Optional[ScheduleConfig]:
        """从 schedule_config 表读取 name=default 配置"""
        result = await self.db.execute(
            select(ScheduleConfig).where(ScheduleConfig.name == "default")
        )
        return result.scalar_one_or_none()

    async def get_next_task(self) -> Optional[Task]:
        """获取下一个 ready 状态任务（含时段和日限额检查）"""
        config = await self._get_schedule_config()
        now = datetime.now(ZoneInfo("Asia/Shanghai")).time()

        if config:
            start_time = time(config.start_hour)
            end_time = time(config.end_hour)
            if not (start_time <= now <= end_time):
                logger.info("当前时间 {} 不在发布时段 {}-{} 内", now, start_time, end_time)
                return None

        # 查询 status=ready 的任务
        query = (
            select(Task)
            .where(Task.status == "ready")
            .order_by(Task.priority.desc(), Task.created_at)
            .limit(1)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task and config:
            # 检查账号当日 uploaded 数量
            task_svc = TaskService(self.db)
            limit_reached = await task_svc.check_account_daily_limit(
                task.account_id, config.max_per_account_per_day
            )
            if limit_reached:
                logger.info("账号 {} 今日发布数已达上限", task.account_id)
                return None

        return task

    async def publish_task(
        self,
        task: Task,
        *,
        post_upload_auth_check: Callable[[], Awaitable[LocalAuthSessionSummary]] | None = None,
    ) -> tuple[bool, str]:
        """发布单个任务"""
        await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )
        self.current_task_id = task.id
        task_svc = TaskService(self.db, auth_summary=self._auth_summary)

        try:
            # 标记为上传中
            await task_svc.mark_task_uploading(task.id)

            # 重新查询并预加载所有关系
            task_result = await self.db.execute(
                select(Task).options(
                    selectinload(Task.videos),
                    selectinload(Task.copywritings),
                    selectinload(Task.audios),
                    selectinload(Task.topics),
                    selectinload(Task.covers),
                ).where(Task.id == task.id)
            )
            task = task_result.scalar_one_or_none()
            if not task:
                return False, "任务不存在"

            # 获取账号
            result = await self.db.execute(
                select(Account).where(Account.id == task.account_id)
            )
            account = result.scalar_one_or_none()

            if not account or account.status != "active":
                await task_svc.mark_task_failed(task.id, "账号无效或未登录")
                return False, "账号无效"

            try:
                execution_view = resolve_publish_execution_view(task)
            except PublishabilityError as exc:
                message = str(exc)
                await task_svc.mark_task_failed(task.id, message)
                logger.warning("任务 {} 不满足 direct publish 语义: {}", task.id, message)
                return False, message

            # 获取得物客户端
            client = await get_dewu_client(account.id)

            # 尝试使用现有上下文或创建新上下文
            context = await browser_manager.get_or_create_context(
                account.id,
                account.storage_state
            )

            if context and context.pages:
                client.page = context.pages[0]
            else:
                client.page = await browser_manager.new_page(account.id)

            # 检查登录状态
            is_logged_in, msg = await client.check_login_status()
            if not is_logged_in:
                await task_svc.mark_task_failed(task.id, "登录已过期")
                return False, "登录已过期"

            # 商品链接已废弃（product_id 不再使用）
            product_link: Optional[str] = None

            # 发布视频
            success, msg = await client.upload_video(
                video_path=execution_view.video_path,
                title=execution_view.content[:50] if execution_view.content else "视频标题",
                content=execution_view.content,
                topic=execution_view.topic,
                cover_path=execution_view.cover_path,
                product_link=product_link
            )

            runtime_summary = (
                await post_upload_auth_check()
                if post_upload_auth_check is not None
                else None
            )
            if runtime_summary and is_runtime_hard_stop_state(runtime_summary.auth_state):
                auth_reason = get_runtime_auth_failure_reason(runtime_summary)
                await task_svc.mark_task_failed(task.id, auth_reason)
                logger.warning(
                    "event_name=publish_task_failed_due_to_auth task_id={} auth_state={} reason_code={}",
                    task.id,
                    runtime_summary.auth_state,
                    auth_reason,
                )
                return False, auth_reason

            if success:
                await task_svc.mark_task_uploaded(task.id)
                logger.info("任务 {} 发布成功", task.id)
                return True, "发布成功"
            else:
                await task_svc.mark_task_failed(task.id, msg)
                logger.error("任务 {} 发布失败: {}", task.id, msg)
                return False, msg

        except Exception as e:
            logger.error("发布任务 {} 异常: {}", task.id, e)
            await task_svc.mark_task_failed(task.id, str(e))
            return False, str(e)

        finally:
            self.current_task_id = None


def get_publish_service(db: AsyncSession) -> PublishService:
    """获取发布服务实例"""
    return PublishService(db)
