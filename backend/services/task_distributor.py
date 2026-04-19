"""
TaskDistributor — 1 份素材集合 x N 个账号 = N 个 Task
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import require_active_service_session
from models import Task
from schemas.auth import LocalAuthSessionSummary
from services.task_assembler import TaskAssembler


class TaskDistributor:
    """为每个账号创建一个 Task，关联相同的素材集合"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self._auth_summary = auth_summary

    async def distribute(
        self,
        video_ids: List[int],
        account_ids: Optional[List[int]],
        copywriting_ids: Optional[List[int]] = None,
        cover_ids: Optional[List[int]] = None,
        audio_ids: Optional[List[int]] = None,
        topic_ids: Optional[List[int]] = None,
        profile_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> List[Task]:
        await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )
        if not video_ids:
            return []

        assembler = TaskAssembler(self.db, auth_summary=self._auth_summary)
        tasks: List[Task] = []
        target_account_ids = account_ids or [None]

        for acct_id in target_account_ids:
            task = await assembler.assemble(
                account_id=acct_id,
                video_ids=video_ids,
                copywriting_ids=copywriting_ids,
                cover_ids=cover_ids,
                audio_ids=audio_ids,
                topic_ids=topic_ids,
                profile_id=profile_id,
                name=name,
            )
            tasks.append(task)

        logger.info(
            "TaskDistributor: 账号数={}, 任务数={}",
            len(target_account_ids), len(tasks),
        )
        return tasks
