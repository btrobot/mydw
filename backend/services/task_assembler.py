"""
SP3-04: TaskAssembler — 为视频组装任务，自动匹配同 product 的文案和话题
SP4-04: 集成全局话题配置
"""
import json
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Copywriting, PublishProfile, Task, TaskTopic, Topic, Video


class TaskAssembler:
    """任务组装器：为视频列表创建任务，自动匹配文案和话题"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def assemble(
        self,
        video_ids: List[int],
        account_id: int,
        copywriting_mode: str = "auto_match",
        profile_id: Optional[int] = None,
        cover_id: Optional[int] = None,
    ) -> List[Task]:
        """
        为每个视频组装任务，自动匹配同 product 的文案和话题。

        Args:
            video_ids: 视频 ID 列表
            account_id: 目标账号 ID
            copywriting_mode: 文案匹配模式，目前支持 "auto_match"
            profile_id: 发布档案 ID，决定初始状态
            cover_id: 封面 ID，应用到所有创建的任务

        Returns:
            创建的 Task 列表
        """
        if not video_ids:
            return []

        # 解析 PublishProfile，决定初始状态
        initial_status = await self._resolve_initial_status(profile_id)

        # 1. 查询 Video，预加载 product 关系
        videos_result = await self.db.execute(
            select(Video)
            .where(Video.id.in_(video_ids))
            .options(selectinload(Video.product))
        )
        videos = videos_result.scalars().all()

        if not videos:
            logger.warning("TaskAssembler: 未找到任何视频, video_ids={}", video_ids)
            return []

        # 2. 收集所有涉及的 product_id，批量查询文案
        product_ids = {v.product_id for v in videos if v.product_id is not None}
        copywritings_by_product: Dict[int, List[Copywriting]] = {}

        if product_ids:
            cw_result = await self.db.execute(
                select(Copywriting).where(Copywriting.product_id.in_(product_ids))
            )
            for cw in cw_result.scalars().all():
                copywritings_by_product.setdefault(cw.product_id, []).append(cw)

        # 3. 读取全局话题配置（从 PublishProfile）
        global_topic_ids: List[int] = []
        profile_for_topics: Optional[PublishProfile] = None

        if profile_id:
            pt_result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.id == profile_id)
            )
            profile_for_topics = pt_result.scalars().first()

        if profile_for_topics is None:
            pt_result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.is_default.is_(True)).limit(1)
            )
            profile_for_topics = pt_result.scalars().first()

        if profile_for_topics and profile_for_topics.global_topic_ids:
            try:
                global_topic_ids = json.loads(profile_for_topics.global_topic_ids)
            except (ValueError, TypeError):
                global_topic_ids = []

        # 查询全局话题对象（保持顺序）
        global_topics: List[Topic] = []
        if global_topic_ids:
            topics_result = await self.db.execute(
                select(Topic).where(Topic.id.in_(global_topic_ids))
            )
            topic_map = {t.id: t for t in topics_result.scalars().all()}
            global_topics = [topic_map[tid] for tid in global_topic_ids if tid in topic_map]

        # 4. 为每个视频创建 Task
        created_tasks: List[Task] = []

        for idx, video in enumerate(videos):
            matched_cw: Optional[Copywriting] = None

            if copywriting_mode == "auto_match" and video.product_id:
                candidates = copywritings_by_product.get(video.product_id, [])
                if candidates:
                    matched_cw = candidates[idx % len(candidates)]

            task = Task(
                video_id=video.id,
                copywriting_id=matched_cw.id if matched_cw else None,
                product_id=video.product_id,
                account_id=account_id,
                profile_id=profile_id,
                cover_id=cover_id,
                status=initial_status,
                priority=0,
                source_video_ids=json.dumps([video.id]),
            )
            self.db.add(task)
            await self.db.flush()  # 获取 task.id，用于创建 TaskTopic

            # 5. 创建 TaskTopic 关联（全局话题）
            for topic in global_topics:
                self.db.add(TaskTopic(task_id=task.id, topic_id=topic.id))

            created_tasks.append(task)
            logger.info(
                "TaskAssembler: 组装任务 task_id={}, video_id={}, account_id={}, copywriting_id={}, status={}",
                task.id,
                video.id,
                account_id,
                matched_cw.id if matched_cw else None,
                initial_status,
            )

        await self.db.commit()

        # 重新查询以预加载关系，避免 lazy loading MissingGreenlet
        task_ids = [task.id for task in created_tasks]
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.topics),
                selectinload(Task.video),
                selectinload(Task.copywriting),
                selectinload(Task.product),
                selectinload(Task.cover),
            ).where(Task.id.in_(task_ids))
        )
        created_tasks = list(result.scalars().all())

        logger.info(
            "TaskAssembler: 完成组装, 共创建 {} 个任务, account_id={}, initial_status={}",
            len(created_tasks),
            account_id,
            initial_status,
        )
        return created_tasks

    async def _resolve_initial_status(self, profile_id: Optional[int]) -> str:
        """
        根据 PublishProfile.composition_mode 决定任务初始状态。
        composition_mode == 'none' → 'ready'，其他 → 'draft'
        无 profile 时默认 'ready'。
        """
        profile: Optional[PublishProfile] = None

        if profile_id:
            result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.id == profile_id)
            )
            profile = result.scalars().first()
            if not profile:
                logger.warning("TaskAssembler: profile_id={} 不存在，回退到默认档案", profile_id)

        if profile is None:
            result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.is_default.is_(True)).limit(1)
            )
            profile = result.scalars().first()

        if profile is None or profile.composition_mode == "none":
            return "ready"

        return "draft"
