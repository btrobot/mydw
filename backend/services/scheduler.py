"""
Scheduler runtime services.
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Literal, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import (
    get_current_auth_summary,
    get_runtime_auth_failure_reason,
    is_runtime_grace_state,
    is_runtime_hard_stop_state,
    load_machine_session_summary,
)
from core.auth_events import auth_event_emitter
from core.config import settings
from models import CompositionJob, ScheduleConfig, Task
from schemas.auth import LocalAuthSessionSummary
from services.schedule_config_service import ScheduleConfigService

RuntimeAuthAction = Literal["allow", "pause", "stop"]


@dataclass(frozen=True)
class RuntimeAuthDecision:
    action: RuntimeAuthAction
    summary: LocalAuthSessionSummary
    reason_code: str | None = None


class RuntimeAuthHalt(Exception):
    def __init__(self, decision: RuntimeAuthDecision) -> None:
        super().__init__(decision.reason_code or decision.summary.auth_state)
        self.decision = decision


class TaskScheduler:
    """Task scheduler with auth-aware runtime enforcement."""

    def __init__(self) -> None:
        self._loop_task: Optional[asyncio.Task] = None
        self._paused: bool = False
        self._pause_reason: Optional[str] = None
        self._current_task_id: Optional[int] = None
        self._last_selection_report: dict | None = None

    def is_running(self) -> bool:
        return self._loop_task is not None and not self._loop_task.done()

    def is_paused(self) -> bool:
        return self._paused

    def current_task_id(self) -> Optional[int]:
        return self._current_task_id

    def get_last_selection_report(self) -> dict | None:
        return self._last_selection_report

    def get_status(self) -> str:
        if self.is_paused():
            return "paused"
        if self.is_running():
            return "running"
        return "idle"

    async def start_publishing(self) -> dict:
        if self.is_running():
            logger.warning("发布任务已在运行")
            return {"success": False, "message": "发布任务已在运行"}

        decision = await self._load_runtime_auth_decision_from_new_session()
        if decision.action != "allow":
            self._current_task_id = None
            if decision.action == "pause":
                self._set_paused(decision.reason_code)
            else:
                self._clear_paused()
            # Emit scheduler denied by auth event
            auth_event_emitter.scheduler_denied_by_auth(
                auth_state=decision.summary.auth_state,
                reason_code=decision.reason_code or "auth_denied",
            )
            return {
                "success": False,
                "message": "当前授权状态不允许启动发布任务",
                "auth_state": decision.summary.auth_state,
                "reason_code": decision.reason_code,
            }

        self._clear_paused()
        self._loop_task = asyncio.create_task(self._publish_loop())
        logger.info("发布任务已启动")
        return {"success": True, "message": "发布任务已启动"}

    async def _publish_loop(self) -> None:
        try:
            from services.publish_service import PublishService
            import models as _models

            while True:
                try:
                    config: Optional[ScheduleConfig] = None
                    async with _models.async_session() as db:
                        decision = await self._load_runtime_auth_decision(db)
                        if decision.action == "pause":
                            self._current_task_id = None
                            self._set_paused(decision.reason_code)
                            # Emit background stopped due to auth event
                            auth_event_emitter.background_stopped_due_to_auth(
                                component="task_scheduler",
                                auth_state=decision.summary.auth_state,
                                reason_code=decision.reason_code or "auth_pause",
                            )
                            return
                        if decision.action == "stop":
                            self._current_task_id = None
                            self._clear_paused()
                            # Emit background stopped due to auth event
                            auth_event_emitter.background_stopped_due_to_auth(
                                component="task_scheduler",
                                auth_state=decision.summary.auth_state,
                                reason_code=decision.reason_code or "auth_stop",
                            )
                            return

                        self._clear_paused()
                        config = await self._get_schedule_config(db)
                        service = PublishService(db)
                        task = await service.get_next_task()
                        selection_report = service.get_last_selection_report()
                        self._last_selection_report = (
                            selection_report.to_dict() if selection_report is not None else None
                        )

                        if not task:
                            self._current_task_id = None
                            await asyncio.sleep(10)
                            continue

                        self._current_task_id = task.id
                        
                        # Check auth before publishing
                        pre_decision = await self._load_runtime_auth_decision(db)
                        if pre_decision.action != "allow":
                            # Emit publish task failed due to auth event
                            auth_event_emitter.publish_task_failed_due_to_auth(
                                task_id=task.id,
                                auth_state=pre_decision.summary.auth_state,
                                reason_code=pre_decision.reason_code or "auth_denied",
                            )
                            self._current_task_id = None
                            await asyncio.sleep(10)
                            continue
                        
                        await service.publish_task(
                            task,
                            post_upload_auth_check=lambda: self._load_runtime_auth_summary(db),
                        )

                        self._current_task_id = None

                        post_decision = await self._load_runtime_auth_decision(db)
                        if post_decision.action == "pause":
                            self._set_paused(post_decision.reason_code)
                            # Emit background stopped due to auth event
                            auth_event_emitter.background_stopped_due_to_auth(
                                component="task_scheduler",
                                auth_state=post_decision.summary.auth_state,
                                reason_code=post_decision.reason_code or "auth_pause_post",
                            )
                            return
                        if post_decision.action == "stop":
                            self._clear_paused()
                            # Emit background stopped due to auth event
                            auth_event_emitter.background_stopped_due_to_auth(
                                component="task_scheduler",
                                auth_state=post_decision.summary.auth_state,
                                reason_code=post_decision.reason_code or "auth_stop_post",
                            )
                            return

                        if config and config.shuffle:
                            await self._shuffle_ready_tasks(db)

                    interval = (config.interval_minutes if config else 30) * 60
                    logger.info(
                        "等待 {} 分钟后继续...",
                        config.interval_minutes if config else 30,
                    )
                    await asyncio.sleep(interval)

                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.error("发布循环单次迭代异常: error_type={}", type(exc).__name__)
                    await asyncio.sleep(10)

        except asyncio.CancelledError:
            self._current_task_id = None
            logger.info("发布循环已取消")

    async def _get_schedule_config(self, db: AsyncSession) -> Optional[ScheduleConfig]:
        service = ScheduleConfigService(db)
        return await service.get_default()

    async def pause_publishing(self) -> dict:
        if self.is_running():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        self._loop_task = None
        self._current_task_id = None
        self._set_paused("manual_pause")
        logger.info("发布任务已暂停")
        return {"success": True, "message": "发布任务已暂停"}

    async def stop_publishing(self) -> dict:
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            logger.info("发布任务已停止")

        self._loop_task = None
        self._current_task_id = None
        self._clear_paused()
        self._last_selection_report = None
        return {"success": True, "message": "发布任务已停止"}

    async def shuffle_tasks(self, db: AsyncSession) -> dict:
        try:
            result = await db.execute(select(Task).where(Task.status == "ready"))
            tasks = result.scalars().all()

            if not tasks:
                return {"success": True, "message": "没有待发布任务"}

            for task in tasks:
                task.priority = random.randint(1, 100)

            await db.commit()
            logger.info("已打乱 {} 个任务", len(tasks))
            return {"success": True, "message": f"已打乱 {len(tasks)} 个任务"}

        except Exception as exc:  # noqa: BLE001
            logger.error("打乱任务失败: error_type={}", type(exc).__name__)
            return {"success": False, "message": str(exc)}

    async def _shuffle_ready_tasks(self, db: AsyncSession) -> None:
        result = await db.execute(select(Task).where(Task.status == "ready"))
        tasks = result.scalars().all()

        for task in tasks:
            task.priority = random.randint(1, 100)

        await db.commit()

    async def _load_runtime_auth_summary(self, db: AsyncSession) -> LocalAuthSessionSummary:
        return await load_machine_session_summary(db)

    async def _load_runtime_auth_decision(self, db: AsyncSession) -> RuntimeAuthDecision:
        summary = await self._load_runtime_auth_summary(db)
        return self._build_runtime_auth_decision(summary)

    async def _load_runtime_auth_decision_from_new_session(self) -> RuntimeAuthDecision:
        import models as _models

        if _models.async_session is None:
            current_summary = get_current_auth_summary()
            if current_summary is not None:
                return self._build_runtime_auth_decision(current_summary)
            return self._build_runtime_auth_decision(
                LocalAuthSessionSummary(auth_state="unauthenticated")
            )

        async with _models.async_session() as db:
            return await self._load_runtime_auth_decision(db)

    def _set_paused(self, reason_code: str | None) -> None:
        self._paused = True
        self._pause_reason = reason_code

    def _clear_paused(self) -> None:
        self._paused = False
        self._pause_reason = None

    @staticmethod
    def _build_runtime_auth_decision(summary: LocalAuthSessionSummary) -> RuntimeAuthDecision:
        if summary.auth_state == "authenticated_active":
            return RuntimeAuthDecision(action="allow", summary=summary)
        if is_runtime_grace_state(summary.auth_state):
            return RuntimeAuthDecision(
                action="pause",
                summary=summary,
                reason_code=summary.denial_reason or "offline_grace_restricted",
            )
        if is_runtime_hard_stop_state(summary.auth_state):
            return RuntimeAuthDecision(
                action="stop",
                summary=summary,
                reason_code=get_runtime_auth_failure_reason(summary),
            )
        return RuntimeAuthDecision(
            action="stop",
            summary=summary,
            reason_code=summary.denial_reason or "remote_auth_denied",
        )


class CompositionPoller:
    """Composition poller with auth-aware runtime enforcement."""

    def __init__(self) -> None:
        self._loop_task: Optional[asyncio.Task] = None
        self._running: bool = False

    def is_running(self) -> bool:
        return self._loop_task is not None and not self._loop_task.done()

    async def start(self) -> dict:
        if self.is_running():
            return {"success": False, "message": "Composition poller 已在运行"}

        decision = await self._load_runtime_auth_decision_from_new_session()
        if decision.action != "allow":
            # Emit scheduler denied by auth event
            auth_event_emitter.scheduler_denied_by_auth(
                auth_state=decision.summary.auth_state,
                reason_code=decision.reason_code or "auth_denied",
            )
            return {
                "success": False,
                "message": "当前授权状态不允许启动 composition poller",
                "auth_state": decision.summary.auth_state,
                "reason_code": decision.reason_code,
            }

        self._running = True
        self._loop_task = asyncio.create_task(self._poll_loop())
        logger.info("Composition poller 已启动")
        return {"success": True, "message": "Composition poller 已启动"}

    async def stop(self) -> dict:
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            logger.info("Composition poller 已停止")

        self._running = False
        self._loop_task = None
        return {"success": True, "message": "Composition poller 已停止"}

    async def _poll_loop(self) -> None:
        try:
            import models as _models
            from services.composition_service import CompositionService
            from core.coze_client import CozeClient

            while self._running:
                try:
                    async with _models.async_session() as db:
                        decision = await self._load_runtime_auth_decision(db)
                        if decision.action != "allow":
                            # Emit composition poller stopped due to auth event
                            auth_event_emitter.composition_poller_stopped_due_to_auth(
                                auth_state=decision.summary.auth_state,
                                reason_code=decision.reason_code or "auth_denied",
                            )
                            self._running = False
                            return

                        await self._poll_compositions(db, CompositionService, CozeClient)

                    await asyncio.sleep(30)

                except asyncio.CancelledError:
                    raise
                except RuntimeAuthHalt as halt:
                    # Emit composition poller stopped due to auth event
                    auth_event_emitter.composition_poller_stopped_due_to_auth(
                        auth_state=halt.decision.summary.auth_state,
                        reason_code=halt.decision.reason_code or "auth_halt",
                    )
                    self._running = False
                    return
                except Exception as exc:  # noqa: BLE001
                    logger.error("Composition poll 异常: error_type={}", type(exc).__name__)
                    await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("Composition poll 循环已取消")

    async def _poll_compositions(
        self,
        db: AsyncSession,
        composition_service_cls: type,
        coze_client_cls: type,
    ) -> None:
        pre_decision = await self._load_runtime_auth_decision(db)
        if pre_decision.action != "allow":
            raise RuntimeAuthHalt(pre_decision)

        job_result = await db.execute(
            select(CompositionJob)
            .where(CompositionJob.task_id == self._get_current_task_id())
            .order_by(CompositionJob.id.desc())
            .limit(1)
        )
        job = job_result.scalars().first()

        if not job:
            return

        if not job.workflow_id or not job.external_job_id:
            return

        coze = coze_client_cls()
        status, output = await coze.check_status(job.workflow_id, job.external_job_id)

        post_decision = await self._load_runtime_auth_decision(db)
        if post_decision.action != "allow":
            raise RuntimeAuthHalt(post_decision)

        service = composition_service_cls(db)

        if "success" in status.lower():
            await service.handle_success(job.id, output or {})
        elif "fail" in status.lower() or "error" in status.lower():
            await service.handle_failure(job.id, f"Coze 工作流执行失败: status={status}")

    def _get_current_task_id(self) -> Optional[int]:
        # This would need to be implemented based on your actual task tracking
        return None

    async def _load_runtime_auth_summary(self, db: AsyncSession) -> LocalAuthSessionSummary:
        return await load_machine_session_summary(db)

    async def _load_runtime_auth_decision(self, db: AsyncSession) -> RuntimeAuthDecision:
        summary = await self._load_runtime_auth_summary(db)
        return self._build_runtime_auth_decision(summary)

    async def _load_runtime_auth_decision_from_new_session(self) -> RuntimeAuthDecision:
        import models as _models

        if _models.async_session is None:
            current_summary = get_current_auth_summary()
            if current_summary is not None:
                return self._build_runtime_auth_decision(current_summary)
            return self._build_runtime_auth_decision(
                LocalAuthSessionSummary(auth_state="unauthenticated")
            )

        async with _models.async_session() as db:
            return await self._load_runtime_auth_decision(db)

    @staticmethod
    def _build_runtime_auth_decision(summary: LocalAuthSessionSummary) -> RuntimeAuthDecision:
        if summary.auth_state == "authenticated_active":
            return RuntimeAuthDecision(action="allow", summary=summary)
        if is_runtime_grace_state(summary.auth_state):
            return RuntimeAuthDecision(
                action="pause",
                summary=summary,
                reason_code=summary.denial_reason or "offline_grace_restricted",
            )
        if is_runtime_hard_stop_state(summary.auth_state):
            return RuntimeAuthDecision(
                action="stop",
                summary=summary,
                reason_code=get_runtime_auth_failure_reason(summary),
            )
        return RuntimeAuthDecision(
            action="stop",
            summary=summary,
            reason_code=summary.denial_reason or "remote_auth_denied",
        )


class SchedulerManager:
    """Unified manager for task scheduler and composition poller."""

    def __init__(self) -> None:
        self.task_scheduler = TaskScheduler()
        self.composition_poller = CompositionPoller()

    async def start_all(self) -> dict:
        publish_result = await self.task_scheduler.start_publishing()
        poll_result = await self.composition_poller.start()
        logger.info("SchedulerManager: 所有组件已启动")
        return {
            "publish": publish_result,
            "composition_poll": poll_result,
        }

    async def stop_all(self) -> dict:
        publish_result = await self.task_scheduler.stop_publishing()
        poll_result = await self.composition_poller.stop()
        logger.info("SchedulerManager: 所有组件已停止")
        return {
            "publish": publish_result,
            "composition_poll": poll_result,
        }

    def is_running(self) -> dict:
        return {
            "task_scheduler": self.task_scheduler.is_running(),
            "composition_poller": self.composition_poller.is_running(),
        }


scheduler = TaskScheduler()
composition_poller = CompositionPoller()
scheduler_manager = SchedulerManager()
