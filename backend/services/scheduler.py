"""
任务调度服务
"""
import asyncio
import random
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from models import Task, PublishConfig
from models import get_db as _get_db


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._publish_task_id: Optional[int] = None

    async def start_publishing(self, db: AsyncSession):
        """启动发布任务"""
        if self._publish_task_id:
            logger.warning("发布任务已在运行")
            return {"success": False, "message": "发布任务已在运行"}

        # 获取配置
        result = await db.execute(
            select(PublishConfig).where(PublishConfig.name == "default")
        )
        config = result.scalar_one_or_none()

        # 启动后台任务
        self._publish_task_id = id(asyncio.current_task())
        asyncio.create_task(self._publish_loop(db, config))
        asyncio.create_task(self._publish_loop(db, config))

        logger.info("发布任务已启动")
        return {"success": True, "message": "发布任务已启动"}

    async def _publish_loop(self, db: AsyncSession, config: PublishConfig):
        """发布循环"""
        try:
            from services.publish_service import PublishService

            service = PublishService(db)

            while True:
                # 检查暂停状态
                if service.is_paused:
                    await asyncio.sleep(1)
                    continue

                # 获取下一个任务
                task = await service.get_next_task()

                if not task:
                    await asyncio.sleep(10)
                    continue

                # 发布任务
                await service.publish_task(task)

                # 乱序处理
                if config and config.shuffle:
                    await self._shuffle_pending_tasks(db)

                # 等待间隔
                interval = (config.interval_minutes if config else 30) * 60
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("发布循环已取消")
        except Exception as e:
            logger.error(f"发布循环异常: {e}")

    async def pause_publishing(self, db: AsyncSession):
        """暂停发布"""
        logger.info("暂停发布")
        return {"success": True}

    async def stop_publishing(self, db: AsyncSession):
        """停止发布"""
        if self._publish_task_id:
            self._publish_task_id = None
            logger.info("停止发布")
        return {"success": True}

    async def shuffle_tasks(self, db: AsyncSession):
        """打乱待发布任务顺序"""
        try:
            result = await db.execute(
                select(Task).where(Task.status == "pending")
            )
            tasks = result.scalars().all()

            if not tasks:
                return {"success": True, "message": "没有待发布任务"}

            # 打乱优先级
            for task in tasks:
                task.priority = random.randint(1, 100)

            await db.commit()
            logger.info(f"已打乱 {len(tasks)} 个任务")
            return {"success": True, "message": f"已打乱 {len(tasks)} 个任务"}

        except Exception as e:
            logger.error(f"打乱任务失败: {e}")
            return {"success": False, "message": str(e)}

    async def _shuffle_pending_tasks(self, db: AsyncSession):
        """内部方法：打乱待发布任务"""
        result = await db.execute(
            select(Task).where(Task.status == "pending")
        )
        tasks = result.scalars().all()

        for task in tasks:
            task.priority = random.randint(1, 100)

        await db.commit()


# 全局调度器实例
scheduler = TaskScheduler()
