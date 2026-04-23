"""
任务发布服务
"""
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional
from datetime import datetime, time
import random
from zoneinfo import ZoneInfo
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Task, Account, PublishExecutionSnapshot, ScheduleConfig
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
    resolve_publish_execution_view_from_snapshot_payload,
)


@dataclass(frozen=True)
class PublishShadowDiff:
    legacy_task_id: int | None
    pool_item_id: int | None
    pool_task_id: int | None
    differs: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "legacy_task_id": self.legacy_task_id,
            "pool_item_id": self.pool_item_id,
            "pool_task_id": self.pool_task_id,
            "differs": self.differs,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class PublishTaskSelectionReport:
    scheduler_mode: str
    effective_scheduler_mode: str
    publish_pool_kill_switch: bool
    publish_pool_shadow_read: bool
    selected_task_id: int | None
    selected_task_kind: str | None
    selected_pool_item_id: int | None
    shadow_diff: PublishShadowDiff | None = None

    def to_dict(self) -> dict:
        return {
            "scheduler_mode": self.scheduler_mode,
            "effective_scheduler_mode": self.effective_scheduler_mode,
            "publish_pool_kill_switch": self.publish_pool_kill_switch,
            "publish_pool_shadow_read": self.publish_pool_shadow_read,
            "selected_task_id": self.selected_task_id,
            "selected_task_kind": self.selected_task_kind,
            "selected_pool_item_id": self.selected_pool_item_id,
            "shadow_diff": self.shadow_diff.to_dict() if self.shadow_diff is not None else None,
        }


class PublishService:
    """发布服务"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self.current_task_id: Optional[int] = None
        self._auth_summary = auth_summary
        self._last_selection_report: PublishTaskSelectionReport | None = None

    async def _get_schedule_config(self) -> Optional[ScheduleConfig]:
        """从 schedule_config 表读取 name=default 配置"""
        result = await self.db.execute(
            select(ScheduleConfig).where(ScheduleConfig.name == "default")
        )
        return result.scalar_one_or_none()

    def get_last_selection_report(self) -> PublishTaskSelectionReport | None:
        return self._last_selection_report

    async def get_next_task(self) -> Optional[Task]:
        """获取下一个待发布任务（支持 task/pool 双模式 cutover）。"""
        config = await self._get_schedule_config()
        now = datetime.now(ZoneInfo("Asia/Shanghai")).time()
        scheduler_mode = getattr(config, "publish_scheduler_mode", "task") if config is not None else "task"
        kill_switch = bool(getattr(config, "publish_pool_kill_switch", False)) if config is not None else False
        shadow_read = bool(getattr(config, "publish_pool_shadow_read", False)) if config is not None else False
        effective_mode = "task" if kill_switch else scheduler_mode

        if config:
            start_time = time(config.start_hour)
            end_time = time(config.end_hour)
            if not (start_time <= now <= end_time):
                logger.info("当前时间 {} 不在发布时段 {}-{} 内", now, start_time, end_time)
                self._last_selection_report = PublishTaskSelectionReport(
                    scheduler_mode=scheduler_mode,
                    effective_scheduler_mode=effective_mode,
                    publish_pool_kill_switch=kill_switch,
                    publish_pool_shadow_read=shadow_read,
                    selected_task_id=None,
                    selected_task_kind=None,
                    selected_pool_item_id=None,
                )
                return None

        daily_limit = config.max_per_account_per_day if config else None
        legacy_task = None
        if effective_mode == "task" or shadow_read:
            legacy_task = await self._get_next_legacy_ready_task(
                max_per_account_per_day=daily_limit,
            )

        pool_task = None
        pool_item_id = None
        if effective_mode == "pool":
            pool_task, pool_item_id = await self._get_next_pool_mode_task(
                max_per_account_per_day=daily_limit,
            )
        elif shadow_read:
            pool_task, pool_item_id = await self._preview_next_pool_mode_selection(
                max_per_account_per_day=daily_limit,
            )

        shadow_diff = None
        if shadow_read:
            shadow_diff = self._build_shadow_diff(
                legacy_task_id=legacy_task.id if legacy_task is not None else None,
                pool_item_id=pool_item_id,
                pool_task_id=pool_task.id if pool_task is not None else None,
            )
            if shadow_diff.differs:
                logger.info(
                    "publish_scheduler_shadow_diff legacy_task_id={} pool_item_id={} pool_task_id={} reasons={}",
                    shadow_diff.legacy_task_id,
                    shadow_diff.pool_item_id,
                    shadow_diff.pool_task_id,
                    list(shadow_diff.reasons),
                )

        selected_task = pool_task if effective_mode == "pool" else legacy_task
        selected_pool_item_id = pool_item_id if effective_mode == "pool" and pool_task is not None else None
        self._last_selection_report = PublishTaskSelectionReport(
            scheduler_mode=scheduler_mode,
            effective_scheduler_mode=effective_mode,
            publish_pool_kill_switch=kill_switch,
            publish_pool_shadow_read=shadow_read,
            selected_task_id=selected_task.id if selected_task is not None else None,
            selected_task_kind=selected_task.task_kind if selected_task is not None else None,
            selected_pool_item_id=selected_pool_item_id,
            shadow_diff=shadow_diff,
        )

        if selected_task is not None:
            logger.info(
                "publish_scheduler_candidate scheduler_mode={} effective_scheduler_mode={} task_id={} task_kind={} pool_item_id={}",
                scheduler_mode,
                effective_mode,
                selected_task.id,
                selected_task.task_kind,
                selected_pool_item_id,
            )
        return selected_task

    async def _get_next_legacy_ready_task(
        self,
        *,
        max_per_account_per_day: int | None,
    ) -> Optional[Task]:
        query = (
            select(Task)
            .where(Task.status == "ready")
            .order_by(Task.priority.desc(), Task.created_at)
            .limit(1)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task is None or max_per_account_per_day is None:
            return task

        if task.account_id is None:
            return task

        task_svc = TaskService(self.db)
        limit_reached = await task_svc.check_account_daily_limit(
            task.account_id,
            max_per_account_per_day,
        )
        if limit_reached:
            logger.info("账号 {} 今日发布数已达上限", task.account_id)
            return None
        return task

    async def _get_next_pool_mode_task(
        self,
        *,
        max_per_account_per_day: int | None,
    ) -> tuple[Optional[Task], int | None]:
        ready_publish_task, ready_pool_item_id = await self._get_ready_bound_publish_task(
            max_per_account_per_day=max_per_account_per_day,
        )
        if ready_publish_task is not None:
            return ready_publish_task, ready_pool_item_id

        from services.publish_planner_service import PublishPlannerService

        planner = PublishPlannerService(self.db, auth_summary=self._auth_summary)
        preview = await planner.preview_next_pool_candidate(
            max_per_account_per_day=max_per_account_per_day,
        )
        if preview is None:
            return None, None

        planning = await planner.plan_publish_task(
            preview.pool_item_id,
            source_task_id=preview.source_task_id,
        )
        planned_task = await TaskService(self.db, auth_summary=self._auth_summary).get_task(planning.task_id)
        return planned_task, planning.pool_item_id

    async def _preview_next_pool_mode_selection(
        self,
        *,
        max_per_account_per_day: int | None,
    ) -> tuple[Optional[Task], int | None]:
        ready_publish_task, ready_pool_item_id = await self._get_ready_bound_publish_task(
            max_per_account_per_day=max_per_account_per_day,
        )
        if ready_publish_task is not None:
            return ready_publish_task, ready_pool_item_id

        from services.publish_planner_service import PublishPlannerService

        preview = await PublishPlannerService(self.db, auth_summary=self._auth_summary).preview_next_pool_candidate(
            max_per_account_per_day=max_per_account_per_day,
        )
        if preview is None:
            return None, None
        return None, preview.pool_item_id

    async def _get_ready_bound_publish_task(
        self,
        *,
        max_per_account_per_day: int | None,
    ) -> tuple[Optional[Task], int | None]:
        result = await self.db.execute(
            select(Task, PublishExecutionSnapshot.pool_item_id)
            .join(PublishExecutionSnapshot, PublishExecutionSnapshot.task_id == Task.id)
            .where(
                Task.status == "ready",
                Task.task_kind == "publish",
            )
            .order_by(Task.priority.desc(), Task.created_at)
        )
        task_svc = TaskService(self.db, auth_summary=self._auth_summary)
        for task, pool_item_id in result.all():
            if max_per_account_per_day is not None and await task_svc.check_account_daily_limit(
                task.account_id,
                max_per_account_per_day,
            ):
                logger.info("账号 {} 今日发布数已达上限", task.account_id)
                continue
            return task, pool_item_id
        return None, None

    async def _resolve_publish_account(
        self,
        task: Task,
        *,
        task_svc: TaskService,
        max_per_account_per_day: int | None,
    ) -> tuple[Optional[Account], Optional[str]]:
        if task.account_id is not None:
            account = await self.db.get(Account, task.account_id)
            if account is None or account.status != "active":
                return None, "账号无效"
            if max_per_account_per_day is not None and await task_svc.check_account_daily_limit(
                account.id,
                max_per_account_per_day,
            ):
                return None, "账号今日发布数已达上限"
            return account, None

        result = await self.db.execute(
            select(Account)
            .where(Account.status == "active")
            .order_by(Account.id)
        )
        accounts = list(result.scalars().all())
        if not accounts:
            return None, "没有可用发布账号"

        candidates = accounts
        if max_per_account_per_day is not None:
            candidates = []
            for account in accounts:
                if not await task_svc.check_account_daily_limit(account.id, max_per_account_per_day):
                    candidates.append(account)
            if not candidates:
                return None, "没有可用发布账号（今日额度已满）"

        account = random.choice(candidates)
        task.account_id = account.id
        await self.db.flush()
        logger.info("publish_task_assigned_random_account task_id={} account_id={}", task.id, account.id)
        return account, None

    @staticmethod
    def _build_shadow_diff(
        *,
        legacy_task_id: int | None,
        pool_item_id: int | None,
        pool_task_id: int | None,
    ) -> PublishShadowDiff:
        reasons: list[str] = []
        if legacy_task_id != pool_task_id:
            reasons.append("selected_task_mismatch")
        if legacy_task_id is None and pool_item_id is not None:
            reasons.append("pool_candidate_only")
        if legacy_task_id is not None and pool_item_id is None:
            reasons.append("legacy_candidate_only")
        if pool_item_id is not None and pool_task_id is None:
            reasons.append("pool_candidate_requires_planning")

        return PublishShadowDiff(
            legacy_task_id=legacy_task_id,
            pool_item_id=pool_item_id,
            pool_task_id=pool_task_id,
            differs=bool(reasons),
            reasons=tuple(reasons),
        )

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
            await self._log_publish_started(task.id)

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

            snapshot = await self._get_publish_snapshot(task.id)

            config = await self._get_schedule_config()
            daily_limit = config.max_per_account_per_day if config is not None else None
            account, account_error = await self._resolve_publish_account(
                task,
                task_svc=task_svc,
                max_per_account_per_day=daily_limit,
            )
            if account is None:
                message = account_error or "没有可用发布账号"
                await task_svc.mark_task_failed(task.id, message)
                await self._release_pool_lock(task.id, reason=message)
                await self._log_publish_result(task.id, success=False, message=message)
                return False, message

            try:
                if snapshot is not None:
                    execution_view = resolve_publish_execution_view_from_snapshot_payload(
                        snapshot.snapshot_json
                    )
                else:
                    execution_view = resolve_publish_execution_view(task)
            except PublishabilityError as exc:
                message = str(exc)
                await task_svc.mark_task_failed(task.id, message)
                await self._release_pool_lock(task.id, reason=message)
                await self._log_publish_result(task.id, success=False, message=message)
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
                await self._release_pool_lock(task.id, reason="登录已过期")
                await self._log_publish_result(task.id, success=False, message="登录已过期")
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
                await self._release_pool_lock(task.id, reason=auth_reason)
                await self._log_publish_result(task.id, success=False, message=auth_reason)
                logger.warning(
                    "event_name=publish_task_failed_due_to_auth task_id={} auth_state={} reason_code={}",
                    task.id,
                    runtime_summary.auth_state,
                    auth_reason,
                )
                return False, auth_reason

            if success:
                await task_svc.mark_task_uploaded(task.id)
                await self._mark_pool_publish_succeeded(task.id)
                await self._log_publish_result(task.id, success=True, message="发布成功")
                logger.info("任务 {} 发布成功", task.id)
                return True, "发布成功"
            else:
                await task_svc.mark_task_failed(task.id, msg)
                await self._release_pool_lock(task.id, reason=msg)
                await self._log_publish_result(task.id, success=False, message=msg)
                logger.error("任务 {} 发布失败: {}", task.id, msg)
                return False, msg

        except Exception as e:
            logger.error("发布任务 {} 异常: {}", task.id, e)
            await task_svc.mark_task_failed(task.id, str(e))
            await self._release_pool_lock(task.id, reason=str(e))
            await self._log_publish_result(task.id, success=False, message=str(e))
            return False, str(e)

        finally:
            self.current_task_id = None

    async def _log_publish_started(self, task_id: int) -> None:
        from services.publish_planner_service import PublishPlannerService

        task = await self.db.get(Task, task_id)
        snapshot = await PublishPlannerService(self.db, auth_summary=self._auth_summary).get_snapshot_for_task(task_id)
        logger.info(
            "publish_started task_id={} creative_item_id={} creative_version_id={} pool_item_id={} task_kind={} scheduler_mode={}",
            task_id,
            task.creative_item_id if task is not None else None,
            task.creative_version_id if task is not None else None,
            snapshot.pool_item_id if snapshot is not None else None,
            task.task_kind if task is not None else None,
            "pool" if snapshot is not None else "task",
        )

    async def _get_publish_snapshot(self, task_id: int) -> PublishExecutionSnapshot | None:
        result = await self.db.execute(
            select(PublishExecutionSnapshot).where(PublishExecutionSnapshot.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def _release_pool_lock(self, task_id: int, *, reason: str) -> None:
        from services.publish_planner_service import PublishPlannerService

        await PublishPlannerService(self.db, auth_summary=self._auth_summary).release_pool_lock_for_task(
            task_id,
            reason=reason,
        )

    async def _mark_pool_publish_succeeded(self, task_id: int) -> None:
        from services.publish_planner_service import PublishPlannerService

        await PublishPlannerService(self.db, auth_summary=self._auth_summary).mark_publish_succeeded(task_id)

    async def _log_publish_result(self, task_id: int, *, success: bool, message: str) -> None:
        from services.publish_planner_service import PublishPlannerService

        task = await self.db.get(Task, task_id)
        snapshot = await PublishPlannerService(self.db, auth_summary=self._auth_summary).get_snapshot_for_task(task_id)
        event_name = "publish_succeeded" if success else "publish_failed"
        logger.info(
            "{} task_id={} creative_item_id={} creative_version_id={} pool_item_id={} scheduler_mode={} message={}",
            event_name,
            task_id,
            task.creative_item_id if task is not None else None,
            task.creative_version_id if task is not None else None,
            snapshot.pool_item_id if snapshot is not None else None,
            "pool" if snapshot is not None else "task",
            message,
        )



def get_publish_service(db: AsyncSession) -> PublishService:
    """获取发布服务实例"""
    return PublishService(db)
