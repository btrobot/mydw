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

from models import Copywriting, PublishConfig, Task, TaskTopic, Topic, Video


class TaskAssembler:
    """任务组装器：为视频列表创建任务，自动匹配文案和话题"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def assemble(
        self,
        video_ids: List[int],
        account_id: int,
        copywriting_mode: str = "auto_match",
    ) -> List[Task]:
        """
        为每个视频组装任务，自动匹配同 product 的文案和话题。

        Args:
            video_ids: 视频 ID 列表
            account_id: 目标账号 ID
            copywriting_mode: 文案匹配模式，目前支持 "auto_match"

        Returns:
            创建的 Task 列表
        """
        if not video_ids:
            return []

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

        # 3. 读取全局话题配置
        cfg_result = await self.db.execute(select(PublishConfig).limit(1))
        config = cfg_result.scalars().first()
        global_topic_ids: List[int] = []
        if config and config.global_topic_ids:
            try:
                global_topic_ids = json.loads(config.global_topic_ids)
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

            # 双写旧字段 topic（话题名称拼接）
            topic_names: str = " ".join(f"#{t.name}" for t in global_topics) if global_topics else ""

            task = Task(
                video_id=video.id,
                copywriting_id=matched_cw.id if matched_cw else None,
                product_id=video.product_id,
                account_id=account_id,
                # 双写旧字段（双写期兼容）
                video_path=video.file_path,
                content=matched_cw.content if matched_cw else None,
                topic=topic_names or None,
                status="pending",
                priority=0,
            )
            self.db.add(task)
            await self.db.flush()  # 获取 task.id，用于创建 TaskTopic

            # 5. 创建 TaskTopic 关联（全局话题）
            for topic in global_topics:
                self.db.add(TaskTopic(task_id=task.id, topic_id=topic.id))

            created_tasks.append(task)
            logger.info(
                "TaskAssembler: 组装任务 task_id={}, video_id={}, account_id={}, copywriting_id={}",
                task.id,
                video.id,
                account_id,
                matched_cw.id if matched_cw else None,
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
            ).where(Task.id.in_(task_ids))
        )
        created_tasks = list(result.scalars().all())

        logger.info(
            "TaskAssembler: 完成组装, 共创建 {} 个任务, account_id={}",
            len(created_tasks),
            account_id,
        )
        return created_tasks
