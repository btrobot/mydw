"""
TaskAssembler — 创建任务并关联资源集合

重构后逻辑：1 份素材集合 + 1 个账号 = 1 个 Task + N 条关联记录
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth_dependencies import require_active_service_session
from models import (
    PublishProfile, Task,
    TaskVideo, TaskCopywriting, TaskCover, TaskAudio, TaskTopic,
)
from schemas.auth import LocalAuthSessionSummary
from services.task_execution_semantics import validate_task_resource_inputs
from services.topic_semantics import merge_task_topic_ids
from services.topic_relation_service import get_profile_topic_ids


class TaskAssembler:
    """任务组装器：创建任务并批量插入资源关联"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self._auth_summary = auth_summary

    async def assemble(
        self,
        account_id: int,
        video_ids: List[int],
        copywriting_ids: Optional[List[int]] = None,
        cover_ids: Optional[List[int]] = None,
        audio_ids: Optional[List[int]] = None,
        topic_ids: Optional[List[int]] = None,
        profile_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Task:
        """
        创建一个 Task 并关联所有资源。

        Returns:
            创建的 Task（已预加载关系）
        """
        await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )
        # 查询一次 profile，复用
        profile = await self._get_profile(profile_id)
        initial_status = "ready" if (profile is None or profile.composition_mode == "none") else "draft"
        validate_task_resource_inputs(
            video_ids=video_ids,
            copywriting_ids=copywriting_ids,
            cover_ids=cover_ids,
            audio_ids=audio_ids,
            composition_mode=profile.composition_mode if profile else "none",
        )

        # Phase 6 / PR3 baseline:
        # explicit task topics first, then profile-level default topics.
        # `/api/topics/global` and `TopicGroup.topic_ids` are not auto-injected here.
        all_topic_ids = merge_task_topic_ids(
            explicit_topic_ids=topic_ids,
            profile_default_topic_ids=await get_profile_topic_ids(self.db, profile),
        )

        # 创建 Task
        task = Task(
            account_id=account_id,
            profile_id=profile_id,
            name=name,
            status=initial_status,
            priority=0,
        )
        self.db.add(task)
        await self.db.flush()

        # 批量插入关联记录
        for order, vid in enumerate(video_ids):
            self.db.add(TaskVideo(task_id=task.id, video_id=vid, sort_order=order))

        for order, cid in enumerate(copywriting_ids or []):
            self.db.add(TaskCopywriting(task_id=task.id, copywriting_id=cid, sort_order=order))

        for order, cid in enumerate(cover_ids or []):
            self.db.add(TaskCover(task_id=task.id, cover_id=cid, sort_order=order))

        for order, aid in enumerate(audio_ids or []):
            self.db.add(TaskAudio(task_id=task.id, audio_id=aid, sort_order=order))

        for tid in all_topic_ids:
            self.db.add(TaskTopic(task_id=task.id, topic_id=tid))

        await self.db.commit()

        # 重新查询预加载关系
        result = await self.db.execute(
            select(Task).options(
                selectinload(Task.videos),
                selectinload(Task.copywritings),
                selectinload(Task.covers),
                selectinload(Task.audios),
                selectinload(Task.topics),
                selectinload(Task.account),
            ).where(Task.id == task.id)
        )
        task = result.scalars().first()

        logger.info(
            "TaskAssembler: task_id={}, account_id={}, videos={}, copywritings={}, covers={}, audios={}, topics={}, status={}",
            task.id, account_id,
            len(video_ids), len(copywriting_ids or []),
            len(cover_ids or []), len(audio_ids or []),
            len(all_topic_ids), initial_status,
        )
        return task

    async def _get_profile(self, profile_id: Optional[int]) -> Optional[PublishProfile]:
        """获取 profile，无则回退到默认。"""
        if profile_id:
            result = await self.db.execute(
                select(PublishProfile).where(PublishProfile.id == profile_id)
            )
            profile = result.scalars().first()
            if profile:
                return profile

        result = await self.db.execute(
            select(PublishProfile).where(PublishProfile.is_default.is_(True)).limit(1)
        )
        return result.scalars().first()
