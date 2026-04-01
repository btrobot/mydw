"""
任务服务
"""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from loguru import logger

from models import Task, Account, Material, Product, PublishLog, PublishConfig


class TaskService:
    """任务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: dict) -> Task:
        """创建单个任务"""
        task = Task(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        logger.info(f"创建任务: ID={task.id}")
        return task

    async def create_tasks_batch(self, tasks_data: List[dict]) -> Tuple[int, List[Task]]:
        """批量创建任务"""
        tasks = [Task(**data) for data in tasks_data]
        self.db.add_all(tasks)
        await self.db.commit()

        # 刷新所有任务
        for task in tasks:
            await self.db.refresh(task)

        logger.info(f"批量创建任务: {len(tasks)} 个")
        return len(tasks), tasks

    async def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        status: str = None,
        account_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[int, List[Task]]:
        """获取任务列表"""
        query = select(Task)

        if status:
            query = query.where(Task.status == status)
        if account_id:
            query = query.where(Task.account_id == account_id)

        # 获取总数
        count_query = select(func.count(Task.id))
        if status:
            count_query = count_query.where(Task.status == status)
        if account_id:
            count_query = count_query.where(Task.account_id == account_id)

        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # 分页查询
        query = query.order_by(Task.priority.desc(), Task.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return total_count, list(tasks)

    async def update_task(self, task_id: int, update_data: dict) -> Optional[Task]:
        """更新任务"""
        task = await self.get_task(task_id)
        if not task:
            return None

        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)

        task.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        task = await self.get_task(task_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True

    async def delete_all_tasks(self, status: str = None) -> int:
        """删除所有任务"""
        query = select(Task)
        if status:
            query = query.where(Task.status == status)

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        count = len(tasks)

        for task in tasks:
            await self.db.delete(task)

        await self.db.commit()
        logger.info(f"删除任务: {count} 个")
        return count

    async def get_next_pending_task(self, account_id: int = None) -> Optional[Task]:
        """获取下一个待发布任务"""
        query = select(Task).where(Task.status == "pending")

        if account_id:
            query = query.where(Task.account_id == account_id)

        query = query.order_by(Task.priority.desc(), Task.created_at)
        query = query.limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def mark_task_running(self, task_id: int) -> Optional[Task]:
        """标记任务为运行中"""
        return await self.update_task(task_id, {"status": "running"})

    async def mark_task_success(self, task_id: int) -> Optional[Task]:
        """标记任务为成功"""
        task = await self.update_task(task_id, {
            "status": "success",
            "publish_time": datetime.utcnow(),
            "error_msg": None
        })

        if task:
            # 创建发布日志
            log = PublishLog(
                task_id=task.id,
                account_id=task.account_id,
                status="success",
                message="发布成功"
            )
            self.db.add(log)
            await self.db.commit()

        return task

    async def mark_task_failed(self, task_id: int, error_msg: str) -> Optional[Task]:
        """标记任务为失败"""
        task = await self.update_task(task_id, {
            "status": "failed",
            "error_msg": error_msg
        })

        if task:
            # 创建发布日志
            log = PublishLog(
                task_id=task.id,
                account_id=task.account_id,
                status="failed",
                message=error_msg
            )
            self.db.add(log)
            await self.db.commit()

        return task

    async def get_task_stats(self) -> dict:
        """获取任务统计"""
        stats = {}

        # 各状态数量
        for status in ['pending', 'running', 'success', 'failed', 'paused']:
            result = await self.db.execute(
                select(func.count(Task.id)).where(Task.status == status)
            )
            stats[status] = result.scalar() or 0

        # 总数
        result = await self.db.execute(select(func.count(Task.id)))
        stats['total'] = result.scalar() or 0

        # 今日发布
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.status == "success",
                Task.publish_time >= today_start
            )
        )
        stats['today_success'] = result.scalar() or 0

        return stats

    async def check_account_daily_limit(self, account_id: int, limit: int = 5) -> bool:
        """检查账号当日发布数是否达到上限"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.account_id == account_id,
                Task.status == "success",
                Task.publish_time >= today_start
            )
        )
        count = result.scalar() or 0

        return count >= limit

    async def auto_generate_tasks(
        self,
        account_id: int,
        video_pattern: str = None,
        count: int = 10
    ) -> Tuple[int, List[Task]]:
        """
        自动生成任务（基于素材）
        """
        # 获取素材
        videos = await self.db.execute(
            select(Material).where(Material.type == "video").limit(count)
        )
        videos = videos.scalars().all()

        texts = await self.db.execute(
            select(Material).where(Material.type == "text")
        )
        texts = texts.scalars().all()

        topics = await self.db.execute(
            select(Material).where(Material.type == "topic")
        )
        topics = topics.scalars().all()

        # 生成任务
        tasks_data = []
        for i, video in enumerate(videos):
            task_data = {
                "account_id": account_id,
                "video_path": video.path,
                "content": texts[i % len(texts)].content if texts else "",
                "topic": topics[i % len(topics)].content if topics else "",
                "status": "pending",
                "priority": 0
            }
            tasks_data.append(task_data)

        return await self.create_tasks_batch(tasks_data)
