"""
任务服务
"""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
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
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.video),
                selectinload(Task.copywriting),
                selectinload(Task.product),
            ).where(Task.id == task.id)
        )
        task = result.scalars().first()
        logger.info("创建任务: ID={}", task.id)
        return task

    async def create_tasks_batch(self, tasks_data: List[dict]) -> Tuple[int, List[Task]]:
        """批量创建任务"""
        tasks = [Task(**data) for data in tasks_data]
        self.db.add_all(tasks)
        await self.db.commit()

        # 重新查询以预加载关系，避免 lazy loading MissingGreenlet
        task_ids = [task.id for task in tasks]
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.video),
                selectinload(Task.copywriting),
                selectinload(Task.product),
            ).where(Task.id.in_(task_ids))
        )
        loaded_tasks = result.scalars().all()

        logger.info("批量创建任务: {} 个", len(loaded_tasks))
        return len(loaded_tasks), list(loaded_tasks)

    async def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        status: Optional[str] = None,
        account_id: Optional[int] = None,
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

    async def delete_all_tasks(self, status: Optional[str] = None) -> int:
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
        logger.info("删除任务: {} 个", count)
        return count

    async def get_next_pending_task(self, account_id: Optional[int] = None) -> Optional[Task]:
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

    async def _match_content_and_topics(self, videos: List[Material]) -> List[dict]:
        """
        为视频列表匹配文案和话题，返回每个视频对应的 {content, topic} 列表。

        文案优先按 product_id 匹配，无关联时轮询无商品文案。
        话题按索引轮询。
        """
        texts_result = await self.db.execute(select(Material).where(Material.type == "text"))
        texts = texts_result.scalars().all()
        texts_by_product: dict = {}
        texts_no_product: list = []
        for t in texts:
            if t.product_id:
                texts_by_product.setdefault(t.product_id, []).append(t)
            else:
                texts_no_product.append(t)

        topics_result = await self.db.execute(select(Material).where(Material.type == "topic"))
        topics = topics_result.scalars().all()

        result = []
        for i, video in enumerate(videos):
            content = ""
            if video.product_id and video.product_id in texts_by_product:
                matched = texts_by_product[video.product_id]
                content = matched[i % len(matched)].content or ""
            elif texts_no_product:
                content = texts_no_product[i % len(texts_no_product)].content or ""

            topic = topics[i % len(topics)].content if topics else ""
            result.append({"content": content, "topic": topic})

        return result

    async def auto_generate_tasks(
        self,
        account_id: int,
        video_pattern: Optional[str] = None,
        count: int = 10
    ) -> Tuple[int, List[Task]]:
        """
        自动生成任务（基于素材，智能关联商品）

        优先使用有 product_id 的视频素材，文案按 product_id 匹配。
        """
        videos_q = select(Material).where(Material.type == "video")
        videos_result = await self.db.execute(
            videos_q.order_by(Material.product_id.isnot(None).desc(), Material.created_at.desc()).limit(count)
        )
        videos = list(videos_result.scalars().all())

        if not videos:
            return 0, []

        matched = await self._match_content_and_topics(videos)
        tasks_data = [
            {
                "account_id": account_id,
                "video_path": video.path,
                "material_id": video.id,
                "product_id": video.product_id,
                "content": matched[i]["content"],
                "topic": matched[i]["topic"],
                "status": "pending",
                "priority": 0,
            }
            for i, video in enumerate(videos)
        ]

        return await self.create_tasks_batch(tasks_data)

    async def init_from_materials(
        self,
        account_id: int,
        count: int = 10
    ) -> Tuple[int, List[Task]]:
        """
        从素材初始化任务 — 只使用未被 pending 任务引用的视频素材。
        """
        from sqlalchemy import and_

        # 找出已被 pending 任务引用的 video_path
        used_paths_q = select(Task.video_path).where(
            and_(Task.status == "pending", Task.video_path.isnot(None))
        )
        used_result = await self.db.execute(used_paths_q)
        used_paths = {r[0] for r in used_result}

        videos_q = select(Material).where(Material.type == "video")
        videos_result = await self.db.execute(
            videos_q.order_by(Material.product_id.isnot(None).desc(), Material.created_at.desc())
        )
        all_videos = videos_result.scalars().all()
        videos = [v for v in all_videos if v.path not in used_paths][:count]

        if not videos:
            return 0, []

        matched = await self._match_content_and_topics(videos)
        tasks_data = [
            {
                "account_id": account_id,
                "video_path": video.path,
                "material_id": video.id,
                "product_id": video.product_id,
                "content": matched[i]["content"],
                "topic": matched[i]["topic"],
                "status": "pending",
                "priority": 0,
            }
            for i, video in enumerate(videos)
        ]

        return await self.create_tasks_batch(tasks_data)
