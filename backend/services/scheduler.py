"""
任务调度服务
"""
import asyncio
import random
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Task, ScheduleConfig


class TaskScheduler:
    """任务调度器（单循环设计）"""

    def __init__(self) -> None:
        self._loop_task: Optional[asyncio.Task] = None

    def is_running(self) -> bool:
        """是否正在运行"""
        return self._loop_task is not None and not self._loop_task.done()

    async def start_publishing(self, db: AsyncSession) -> dict:
        """启动发布任务"""
        if self.is_running():
            logger.warning("发布任务已在运行")
            return {"success": False, "message": "发布任务已在运行"}

        self._loop_task = asyncio.create_task(self._publish_loop(db))
        logger.info("发布任务已启动")
        return {"success": True, "message": "发布任务已启动"}

    async def _publish_loop(self, db: AsyncSession) -> None:
        """单循环：从 status=ready 取任务并发布"""
        try:
            from services.publish_service import PublishService

            service = PublishService(db)

            while True:
                # 获取调度配置
                config = await self._get_schedule_config(db)

                # 获取下一个 ready 任务
                task = await service.get_next_task()

                if not task:
                    await asyncio.sleep(10)
                    continue

                # 发布任务
                await service.publish_task(task)

                # 乱序处理
                if config and config.shuffle:
                    await self._shuffle_ready_tasks(db)

                # 等待间隔
                interval = (config.interval_minutes if config else 30) * 60
                logger.info("等待 {} 分钟后继续...", config.interval_minutes if config else 30)
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("发布循环已取消")
        except Exception as e:
            logger.error("发布循环异常: {}", e)

    async def _get_schedule_config(self, db: AsyncSession) -> Optional[ScheduleConfig]:
        """读取 schedule_config 表中 name=default 的配置"""
        result = await db.execute(
            select(ScheduleConfig).where(ScheduleConfig.name == "default")
        )
        return result.scalar_one_or_none()

    async def pause_publishing(self, db: AsyncSession) -> dict:
        """暂停发布（预留接口，当前通过 stop/start 实现）"""
        logger.info("暂停发布")
        return {"success": True}

    async def stop_publishing(self, db: AsyncSession) -> dict:
        """停止发布，取消后台 asyncio.Task"""
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            logger.info("发布任务已停止")

        self._loop_task = None
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
            logger.error("打乱任务失败: {}", e)
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


# 全局调度器实例
scheduler = TaskScheduler()
