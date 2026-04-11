"""
任务调度服务
"""
import asyncio
import random
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Task, CompositionJob, ScheduleConfig
from core.config import settings
from services.schedule_config_service import ScheduleConfigService


class TaskScheduler:
    """任务调度器（单循环设计）"""

    def __init__(self) -> None:
        self._loop_task: Optional[asyncio.Task] = None
        self._paused: bool = False
        self._current_task_id: Optional[int] = None

    def is_running(self) -> bool:
        """是否正在运行"""
        return self._loop_task is not None and not self._loop_task.done()

    def is_paused(self) -> bool:
        """是否处于暂停态。"""
        return self._paused

    def current_task_id(self) -> Optional[int]:
        """返回当前发布中的任务 ID。"""
        return self._current_task_id

    def get_status(self) -> str:
        """返回对外暴露的调度器状态。"""
        if self.is_running():
            return "running"
        if self.is_paused():
            return "paused"
        return "idle"

    async def start_publishing(self) -> dict:
        """启动发布任务"""
        if self.is_running():
            logger.warning("发布任务已在运行")
            return {"success": False, "message": "发布任务已在运行"}

        self._paused = False
        self._loop_task = asyncio.create_task(self._publish_loop())
        logger.info("发布任务已启动")
        return {"success": True, "message": "发布任务已启动"}

    async def _publish_loop(self) -> None:
        """单循环：从 status=ready 取任务并发布，每轮创建新 session"""
        try:
            from services.publish_service import PublishService
            import models as _models

            while True:
                try:
                    config: Optional[ScheduleConfig] = None
                    async with _models.async_session() as db:
                        config = await self._get_schedule_config(db)
                        service = PublishService(db)
                        task = await service.get_next_task()

                        if not task:
                            self._current_task_id = None
                            await asyncio.sleep(10)
                            continue

                        self._current_task_id = task.id
                        await service.publish_task(task)
                        self._current_task_id = None

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
                except Exception as e:
                    logger.error("发布循环单次迭代异常: error_type={}", type(e).__name__)
                    await asyncio.sleep(10)

        except asyncio.CancelledError:
            self._current_task_id = None
            logger.info("发布循环已取消")

    async def _get_schedule_config(self, db: AsyncSession) -> Optional[ScheduleConfig]:
        """读取默认调度配置（通过 canonical access service）。"""
        service = ScheduleConfigService(db)
        return await service.get_default()

    async def pause_publishing(self) -> dict:
        """暂停发布，并保留 paused 状态供后续恢复。"""
        if self.is_running():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        self._loop_task = None
        self._current_task_id = None
        self._paused = True
        logger.info("发布任务已暂停")
        return {"success": True, "message": "发布任务已暂停"}

    async def stop_publishing(self) -> dict:
        """停止发布，取消后台 asyncio.Task"""
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            logger.info("发布任务已停止")

        self._loop_task = None
        self._current_task_id = None
        self._paused = False
        return {"success": True, "message": "发布任务已停止"}

    async def shuffle_tasks(self, db: AsyncSession) -> dict:
        """打乱 ready 状态任务顺序"""
        try:
            result = await db.execute(
                select(Task).where(Task.status == "ready")
            )
            tasks = result.scalars().all()

            if not tasks:
                return {"success": True, "message": "没有待发布任务"}

            for task in tasks:
                task.priority = random.randint(1, 100)

            await db.commit()
            logger.info("已打乱 {} 个任务", len(tasks))
            return {"success": True, "message": f"已打乱 {len(tasks)} 个任务"}

        except Exception as e:
            logger.error("打乱任务失败: error_type={}", type(e).__name__)
            return {"success": False, "message": str(e)}

    async def _shuffle_ready_tasks(self, db: AsyncSession) -> None:
        """内部方法：打乱 ready 状态任务优先级"""
        result = await db.execute(
            select(Task).where(Task.status == "ready")
        )
        tasks = result.scalars().all()

        for task in tasks:
            task.priority = random.randint(1, 100)

        await db.commit()


class CompositionPoller:
    """合成任务轮询器：定期检查 status=composing 的任务并更新状态"""

    BATCH_SIZE: int = 10

    def __init__(self) -> None:
        self._poll_task: Optional[asyncio.Task] = None

    def is_running(self) -> bool:
        """是否正在运行"""
        return self._poll_task is not None and not self._poll_task.done()

    async def start(self) -> dict:
        """启动轮询"""
        if self.is_running():
            logger.warning("合成轮询已在运行")
            return {"success": False, "message": "合成轮询已在运行"}

        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("合成轮询已启动")
        return {"success": True, "message": "合成轮询已启动"}

    async def stop(self) -> dict:
        """停止轮询"""
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            logger.info("合成轮询已停止")

        self._poll_task = None
        return {"success": True, "message": "合成轮询已停止"}

    async def _poll_loop(self) -> None:
        """轮询主循环：每轮创建新 session，单次迭代异常不终止循环"""
        try:
            import models as _models
            from services.composition_service import CompositionService
            from core.coze_client import CozeClient

            while True:
                try:
                    async with _models.async_session() as db:
                        await self._poll_once(db, CompositionService, CozeClient)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(
                        "合成轮询单次迭代异常: error_type={}", type(e).__name__
                    )

                await asyncio.sleep(settings.COZE_POLL_INTERVAL)

        except asyncio.CancelledError:
            logger.info("合成轮询循环已取消")

    async def _poll_once(
        self,
        db: AsyncSession,
        composition_service_cls: type,
        coze_client_cls: type,
    ) -> None:
        """单次轮询：查询 composing 任务 → 检查 Coze 状态 → 回调服务"""
        result = await db.execute(
            select(Task)
            .where(Task.status == "composing")
            .limit(self.BATCH_SIZE)
        )
        tasks = result.scalars().all()

        if not tasks:
            return

        logger.debug("合成轮询: 发现 {} 个 composing 任务", len(tasks))

        for task in tasks:
            try:
                await self._check_task(db, task, composition_service_cls, coze_client_cls)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(
                    "合成轮询: task_id={} 检查失败, error_type={}",
                    task.id,
                    type(e).__name__,
                )

    async def _check_task(
        self,
        db: AsyncSession,
        task: Task,
        composition_service_cls: type,
        coze_client_cls: type,
    ) -> None:
        """检查单个任务的合成状态并触发回调"""
        # 查找关联的 CompositionJob（取最新一条）
        job_result = await db.execute(
            select(CompositionJob)
            .where(CompositionJob.task_id == task.id)
            .order_by(CompositionJob.id.desc())
            .limit(1)
        )
        job = job_result.scalars().first()

        if not job:
            logger.warning("合成轮询: task_id={} 无 CompositionJob，跳过", task.id)
            return

        # workflow_id / external_job_id 为 None 时跳过
        if not job.workflow_id or not job.external_job_id:
            logger.debug(
                "合成轮询: task_id={} job_id={} workflow_id 或 external_job_id 为空，跳过",
                task.id,
                job.id,
            )
            return

        coze = coze_client_cls()
        status, output = await coze.check_status(job.workflow_id, job.external_job_id)

        service = composition_service_cls(db)

        if "success" in status.lower():
            logger.info(
                "合成轮询: task_id={} job_id={} 完成，触发 handle_success",
                task.id,
                job.id,
            )
            await service.handle_success(job.id, output or {})
        elif "fail" in status.lower() or "error" in status.lower():
            logger.warning(
                "合成轮询: task_id={} job_id={} 失败, status={}",
                task.id,
                job.id,
                status,
            )
            await service.handle_failure(job.id, f"Coze 工作流执行失败: status={status}")
        else:
            logger.debug(
                "合成轮询: task_id={} job_id={} 仍在运行, status={}",
                task.id,
                job.id,
                status,
            )


class SchedulerManager:
    """统一管理 TaskScheduler + CompositionPoller"""

    def __init__(self) -> None:
        self.task_scheduler = TaskScheduler()
        self.composition_poller = CompositionPoller()

    async def start_all(self) -> dict:
        """启动所有调度组件"""
        publish_result = await self.task_scheduler.start_publishing()
        poll_result = await self.composition_poller.start()
        logger.info("SchedulerManager: 所有组件已启动")
        return {
            "publish": publish_result,
            "composition_poll": poll_result,
        }

    async def stop_all(self) -> dict:
        """停止所有调度组件"""
        publish_result = await self.task_scheduler.stop_publishing()
        poll_result = await self.composition_poller.stop()
        logger.info("SchedulerManager: 所有组件已停止")
        return {
            "publish": publish_result,
            "composition_poll": poll_result,
        }

    def is_running(self) -> dict:
        """返回各组件运行状态"""
        return {
            "task_scheduler": self.task_scheduler.is_running(),
            "composition_poller": self.composition_poller.is_running(),
        }


# 全局实例
scheduler = TaskScheduler()
composition_poller = CompositionPoller()
scheduler_manager = SchedulerManager()
